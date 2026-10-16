"use strict";

/*
 * Event-driven programming paradigm comparison.
 *
 * This implementation uses Node.js built-in modules only. An event emitter
 * records lifecycle changes, while immutable snapshots prevent listeners
 * from accidentally modifying repository governance state.
 *
 * Run with:
 *   node programming-paradigms.js
 */

const { EventEmitter } = require("node:events");
const { createHash } = require("node:crypto");

class DomainError extends Error {
  constructor(message) {
    super(message);
    this.name = "DomainError";
  }
}

const ReviewState = Object.freeze({
  COMMENTED: "commented",
  APPROVED: "approved",
  CHANGES_REQUESTED: "changes_requested",
});

function requireText(value, label) {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new DomainError(`${label} must be a non-empty string.`);
  }
  return value.trim();
}

function deepFreeze(value) {
  if (value && typeof value === "object" && !Object.isFrozen(value)) {
    Object.freeze(value);
    for (const child of Object.values(value)) {
      deepFreeze(child);
    }
  }
  return value;
}

function makeCommit({ id, author, files, additions, deletions }) {
  const commit = {
    id: requireText(id, "Commit ID"),
    author: requireText(author, "Author"),
    files: [...new Set(files.map((file) => requireText(file, "File path")))],
    additions,
    deletions,
  };

  if (commit.files.length !== files.length) {
    throw new DomainError("Commit contains duplicate file paths.");
  }
  if (commit.files.some((file) => file.startsWith("/") ||
      file.split("/").includes(".."))) {
    throw new DomainError("Commit contains a path outside the repository.");
  }
  if (!Number.isSafeInteger(additions) || additions < 0 ||
      !Number.isSafeInteger(deletions) || deletions < 0) {
    throw new DomainError("Line counts must be non-negative safe integers.");
  }
  if (commit.files.length === 0) {
    throw new DomainError("Commit must modify at least one file.");
  }

  return deepFreeze(commit);
}

function makePullRequest({ id, title, source, target, commits, draft = false }) {
  const pullRequest = {
    id,
    title: requireText(title, "Title"),
    source: requireText(source, "Source branch"),
    target: requireText(target, "Target branch"),
    commits: [...commits],
    draft: Boolean(draft),
    status: "open",
    reviews: [],
    checks: new Map(),
    conversations: [],
    baseRevision: 0,
  };

  if (!Number.isSafeInteger(id) || id <= 0) {
    throw new DomainError("Pull request ID must be a positive integer.");
  }
  if (pullRequest.source === pullRequest.target) {
    throw new DomainError("Source and target branches must differ.");
  }
  if (pullRequest.commits.length === 0) {
    throw new DomainError("Pull request must contain commits.");
  }

  return pullRequest;
}

class RepositoryWorkflow extends EventEmitter {
  #pullRequests = new Map();
  #requiredChecks;
  #requiredApprovals;
  #protectedBranches;
  #revision = 0;

  constructor({
    requiredChecks = ["unit-tests", "security-scan"],
    requiredApprovals = 2,
    protectedBranches = ["main", "release"],
  } = {}) {
    super();

    if (!Number.isInteger(requiredApprovals) || requiredApprovals < 0) {
      throw new DomainError("Approval requirement must be a non-negative integer.");
    }

    this.#requiredChecks = new Set(requiredChecks);
    this.#requiredApprovals = requiredApprovals;
    this.#protectedBranches = new Set(protectedBranches);
  }

  #getOpenRequest(id) {
    const pullRequest = this.#pullRequests.get(id);
    if (!pullRequest) {
      throw new DomainError(`Pull request ${id} does not exist.`);
    }
    if (pullRequest.status !== "open") {
      throw new DomainError("The pull request is not open.");
    }
    return pullRequest;
  }

  #emitChange(type, pullRequest, details = {}) {
    this.#revision += 1;
    const event = deepFreeze({
      type,
      revision: this.#revision,
      pullRequestId: pullRequest.id,
      timestamp: new Date().toISOString(),
      details: { ...details },
    });

    // Listeners receive a frozen event, not the mutable aggregate itself.
    this.emit(type, event);
    this.emit("audit", event);
  }

  open(pullRequest) {
    if (this.#pullRequests.has(pullRequest.id)) {
      throw new DomainError("Pull request ID already exists.");
    }

    this.#pullRequests.set(pullRequest.id, pullRequest);
    this.#emitChange("pull_request.opened", pullRequest, {
      source: pullRequest.source,
      target: pullRequest.target,
      draft: pullRequest.draft,
    });
  }

  markReady(id) {
    const pullRequest = this.#getOpenRequest(id);
    if (!pullRequest.draft) {
      throw new DomainError("Only a draft pull request can be marked ready.");
    }
    pullRequest.draft = false;
    this.#emitChange("pull_request.ready", pullRequest);
  }

  synchronizeBase(id, newRevision) {
    const pullRequest = this.#getOpenRequest(id);
    if (!Number.isSafeInteger(newRevision) ||
        newRevision <= pullRequest.baseRevision) {
      throw new DomainError("Base revision must increase.");
    }

    pullRequest.baseRevision = newRevision;
    this.#emitChange("pull_request.synchronized", pullRequest, {
      baseRevision: newRevision,
    });
  }

  recordCheck(id, name, passed) {
    const pullRequest = this.#getOpenRequest(id);
    requireText(name, "Check name");
    if (typeof passed !== "boolean") {
      throw new DomainError("Check result must be boolean.");
    }

    pullRequest.checks.set(name, passed);
    this.#emitChange("status_check.completed", pullRequest, {
      name,
      passed,
    });
  }

  recordReview(id, review) {
    const pullRequest = this.#getOpenRequest(id);
    const reviewer = requireText(review.reviewer, "Reviewer");
    const commitId = requireText(review.commitId, "Reviewed commit");

    if (!Object.values(ReviewState).includes(review.state)) {
      throw new DomainError("Unsupported review state.");
    }

    const knownCommits = new Set(
      pullRequest.commits.map((commit) => commit.id)
    );
    if (!knownCommits.has(commitId)) {
      throw new DomainError("Review references a commit outside the pull request.");
    }

    pullRequest.reviews.push({
      reviewer,
      commitId,
      state: review.state,
      dismissed: false,
      submittedAt: new Date().toISOString(),
      comments: (review.comments || []).map((comment) =>
        requireText(comment, "Review comment")
      ),
    });

    this.#emitChange("review.submitted", pullRequest, {
      reviewer,
      state: review.state,
      commitId,
    });
  }

  dismissReview(id, reviewer, reason) {
    const pullRequest = this.#getOpenRequest(id);
    requireText(reason, "Dismissal reason");

    const review = [...pullRequest.reviews]
      .reverse()
      .find((candidate) =>
        candidate.reviewer === reviewer && !candidate.dismissed
      );

    if (!review) {
      throw new DomainError("No active review exists for this reviewer.");
    }

    review.dismissed = true;
    this.#emitChange("review.dismissed", pullRequest, {
      reviewer,
      reason,
    });
  }

  addConversation(id, conversation) {
    const pullRequest = this.#getOpenRequest(id);
    const item = {
      id: requireText(conversation.id, "Conversation ID"),
      resolved: false,
      text: requireText(conversation.text, "Conversation text"),
    };

    if (pullRequest.conversations.some((entry) => entry.id === item.id)) {
      throw new DomainError("Conversation ID already exists.");
    }

    pullRequest.conversations.push(item);
    this.#emitChange("conversation.opened", pullRequest, { id: item.id });
  }

  resolveConversation(id, conversationId) {
    const pullRequest = this.#getOpenRequest(id);
    const conversation = pullRequest.conversations.find(
      (item) => item.id === conversationId
    );

    if (!conversation) {
      throw new DomainError("Conversation does not exist.");
    }
    if (conversation.resolved) {
      throw new DomainError("Conversation is already resolved.");
    }

    conversation.resolved = true;
    this.#emitChange("conversation.resolved", pullRequest, {
      id: conversationId,
    });
  }

  evaluate(id) {
    const pullRequest = this.#getOpenRequest(id);
    const reasons = [];

    if (pullRequest.draft) reasons.push("Pull request is a draft.");

    const authors = new Set(pullRequest.commits.map((commit) => commit.author));
    const latestReviews = new Map();

    for (const review of pullRequest.reviews) {
      if (!review.dismissed) latestReviews.set(review.reviewer, review);
    }

    let approvals = 0;
    for (const [reviewer, review] of latestReviews) {
      if (review.state === ReviewState.CHANGES_REQUESTED) {
        reasons.push(`Changes requested by ${reviewer}.`);
      }
      if (review.state === ReviewState.APPROVED) {
        if (authors.has(reviewer)) {
          reasons.push(`Author ${reviewer} cannot approve their own change.`);
        } else {
          approvals += 1;
        }
      }
    }

    if (approvals < this.#requiredApprovals) {
      reasons.push(
        `Requires ${this.#requiredApprovals} approvals; found ${approvals}.`
      );
    }

    for (const name of this.#requiredChecks) {
      if (pullRequest.checks.get(name) !== true) {
        reasons.push(`Required check is missing or failing: ${name}.`);
      }
    }

    if (this.#protectedBranches.has(pullRequest.target) &&
        pullRequest.conversations.some((item) => !item.resolved)) {
      reasons.push("Protected-branch review conversations remain unresolved.");
    }

    return deepFreeze({
      pullRequestId: id,
      eligible: reasons.length === 0,
      reasons,
      evaluatedRevision: this.#revision,
    });
  }

  merge(id) {
    const pullRequest = this.#getOpenRequest(id);
    const decision = this.evaluate(id);

    if (!decision.eligible) {
      throw new DomainError(
        `Merge blocked: ${decision.reasons.join(" ")}`
      );
    }

    pullRequest.status = "merged";
    const result = deepFreeze({
      pullRequestId: id,
      target: pullRequest.target,
      mergeCommit: createHash("sha256")
        .update(`${id}:${pullRequest.target}:${this.#revision}`)
        .digest("hex")
        .slice(0, 12),
    });

    this.#emitChange("pull_request.merged", pullRequest, result);
    return result;
  }

  close(id) {
    const pullRequest = this.#getOpenRequest(id);
    pullRequest.status = "closed";
    this.#emitChange("pull_request.closed", pullRequest);
  }

  snapshot(id) {
    const pullRequest = this.#pullRequests.get(id);
    if (!pullRequest) throw new DomainError("Pull request does not exist.");

    return deepFreeze({
      id: pullRequest.id,
      title: pullRequest.title,
      source: pullRequest.source,
      target: pullRequest.target,
      draft: pullRequest.draft,
      status: pullRequest.status,
      reviews: pullRequest.reviews.map((review) => ({ ...review })),
      checks: Object.fromEntries(pullRequest.checks),
      conversations: pullRequest.conversations.map((item) => ({ ...item })),
      baseRevision: pullRequest.baseRevision,
    });
  }
}

// Functional transformation: derive a risk report without mutating source data.
function summarizeChangedFiles(pullRequest) {
  return pullRequest.commits
    .flatMap((commit) => commit.files.map((file) => ({
      file,
      author: commit.author,
      netLines: commit.additions - commit.deletions,
    })))
    .reduce((summary, item) => {
      const current = summary[item.file] || {
        touches: 0,
        authors: new Set(),
        netLines: 0,
      };

      current.touches += 1;
      current.authors.add(item.author);
      current.netLines += item.netLines;
      summary[item.file] = current;
      return summary;
    }, {});
}

function main() {
  const events = [];
  const workflow = new RepositoryWorkflow({
    requiredApprovals: 2,
    requiredChecks: ["unit-tests", "security-scan"],
    protectedBranches: ["main", "release"],
  });

  workflow.on("audit", (event) => events.push(event));

  const commits = [
    makeCommit({
      id: "c100",
      author: "maya",
      files: ["src/session.js", "tests/session.test.js"],
      additions: 65,
      deletions: 14,
    }),
    makeCommit({
      id: "c101",
      author: "liam",
      files: ["src/session.js", "docs/security.md"],
      additions: 28,
      deletions: 7,
    }),
  ];

  const pullRequest = makePullRequest({
    id: 42,
    title: "Harden session expiry validation",
    source: "feature/session-expiry",
    target: "main",
    commits,
    draft: true,
  });

  workflow.open(pullRequest);
  workflow.markReady(42);
  workflow.synchronizeBase(42, 3);

  workflow.recordCheck(42, "unit-tests", true);
  workflow.recordCheck(42, "security-scan", true);

  workflow.addConversation(42, {
    id: "thread-7",
    text: "Confirm expired tokens are rejected before session lookup.",
  });

  workflow.recordReview(42, {
    reviewer: "olivia",
    state: ReviewState.APPROVED,
    commitId: "c101",
    comments: ["Expiry is validated before session retrieval."],
  });

  workflow.recordReview(42, {
    reviewer: "ethan",
    state: ReviewState.APPROVED,
    commitId: "c101",
  });

  console.log("INITIAL MERGE DECISION");
  console.log(workflow.evaluate(42));

  workflow.resolveConversation(42, "thread-7");

  console.log("\nFINAL MERGE DECISION");
  console.log(workflow.evaluate(42));

  console.log("\nCHANGED-FILE ANALYSIS");
  console.dir(summarizeChangedFiles(pullRequest), { depth: 3 });

  console.log("\nMERGE RESULT");
  console.log(workflow.merge(42));

  console.log("\nAUDIT EVENTS");
  console.log(`Recorded ${events.length} immutable lifecycle events.`);
  console.log(events.map((event) => event.type).join(" -> "));

  console.log("\nFAILURE HANDLING");
  try {
    workflow.merge(42);
  } catch (error) {
    console.log(`${error.name}: ${error.message}`);
  }
}

main();
