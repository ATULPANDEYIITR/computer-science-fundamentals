#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

enum class Permission {
    Read,
    Write,
    Execute
};

struct RepositoryFile {
    fs::path path;
    std::uintmax_t size{};
    fs::perms permissions{fs::perms::unknown};
    bool regular{};
};

class FileSystemPolicy {
public:
    static bool hasPermission(fs::perms permissions, Permission requested) {
        using P = fs::perms;

        if (requested == Permission::Read) {
            return (permissions & P::owner_read) != P::none;
        }
        if (requested == Permission::Write) {
            return (permissions & P::owner_write) != P::none;
        }
        return (permissions & P::owner_exec) != P::none;
    }

    static bool isSafePath(const fs::path& root, const fs::path& candidate) {
        const fs::path rootAbsolute = fs::weakly_canonical(root);
        const fs::path candidateAbsolute = fs::weakly_canonical(candidate);

        auto rootIt = rootAbsolute.begin();
        auto candidateIt = candidateAbsolute.begin();

        for (; rootIt != rootAbsolute.end(); ++rootIt, ++candidateIt) {
            if (candidateIt == candidateAbsolute.end() || *rootIt != *candidateIt) {
                return false;
            }
        }

        return true;
    }
};

class RepositoryWorkspace {
private:
    fs::path root;

public:
    explicit RepositoryWorkspace(fs::path workspace) : root(std::move(workspace)) {
        fs::create_directories(root / "src");
        fs::create_directories(root / "docs");
        fs::create_directories(root / "build" / "logs");
    }

    const fs::path& getRoot() const {
        return root;
    }

    void createFile(const fs::path& relative, const std::string& content) {
        const fs::path target = root / relative;

        if (!FileSystemPolicy::isSafePath(root, target)) {
            throw std::runtime_error("Refusing path outside workspace.");
        }

        fs::create_directories(target.parent_path());

        std::ofstream output(target, std::ios::binary);
        if (!output) {
            throw std::runtime_error("Cannot create file: " + target.string());
        }

        output << content;

        if (!output) {
            throw std::runtime_error("Write failed: " + target.string());
        }
    }

    std::vector<RepositoryFile> inventory() const {
        std::vector<RepositoryFile> files;

        for (const auto& entry : fs::recursive_directory_iterator(root)) {
            if (!entry.is_regular_file()) {
                continue;
            }

            const auto info = entry.status();

            files.push_back({
                entry.path(),
                entry.file_size(),
                info.permissions(),
                true
            });
        }

        std::sort(files.begin(), files.end(),
                  [](const RepositoryFile& left, const RepositoryFile& right) {
                      return left.path < right.path;
                  });

        return files;
    }

    void printInventory() const {
        std::cout << "\nRepository filesystem inventory\n";

        for (const auto& file : inventory()) {
            std::cout
                << "  " << fs::relative(file.path, root)
                << " | " << file.size << " bytes"
                << " | read=" << FileSystemPolicy::hasPermission(
                    file.permissions, Permission::Read)
                << " | write=" << FileSystemPolicy::hasPermission(
                    file.permissions, Permission::Write)
                << '\n';
        }
    }

    void protectBuildLogs() {
        const fs::path logs = root / "build" / "logs";

        std::error_code error;
        fs::permissions(
            logs,
            fs::perms::owner_read |
            fs::perms::owner_write |
            fs::perms::owner_exec |
            fs::perms::group_read |
            fs::perms::group_exec,
            fs::perm_options::replace,
            error
        );

        if (error) {
            throw std::runtime_error(
                "Unable to change directory permissions: " + error.message()
            );
        }
    }

    bool removeSafely(const fs::path& relative) {
        const fs::path target = root / relative;

        if (!FileSystemPolicy::isSafePath(root, target)) {
            throw std::runtime_error("Unsafe deletion target.");
        }

        std::error_code error;
        fs::remove_all(target, error);

        if (error) {
            throw std::runtime_error(
                "Deletion failed: " + error.message()
            );
        }

        return true;
    }
};

struct BackupRecord {
    fs::path original;
    fs::path backup;
    bool completed{};
};

class BackupService {
public:
    static BackupRecord createBackup(
        const fs::path& root,
        const fs::path& source
    ) {
        if (!fs::exists(source) || !fs::is_regular_file(source)) {
            throw std::invalid_argument("Backup source must be a regular file.");
        }

        const fs::path backup = root / "build" / "logs" /
                                (source.stem().string() + ".bak");

        fs::create_directories(backup.parent_path());

        std::error_code error;
        fs::copy_file(
            source,
            backup,
            fs::copy_options::overwrite_existing,
            error
        );

        if (error) {
            throw std::runtime_error(
                "Backup failed: " + error.message()
            );
        }

        return {source, backup, true};
    }
};

void showMetadata(const fs::path& file) {
    const auto info = fs::status(file);

    std::cout << "\nMetadata for " << file.filename() << '\n';
    std::cout << "  Size: " << fs::file_size(file) << " bytes\n";
    std::cout << "  Regular file: " << fs::is_regular_file(info) << '\n';
    std::cout << "  Directory: " << fs::is_directory(info) << '\n';
    std::cout << "  Owner read: "
              << FileSystemPolicy::hasPermission(info.permissions(), Permission::Read)
              << '\n';
    std::cout << "  Owner write: "
              << FileSystemPolicy::hasPermission(info.permissions(), Permission::Write)
              << '\n';
}

int main() {
    try {
        const auto timestamp =
            std::chrono::steady_clock::now().time_since_epoch().count();

        const fs::path root =
            fs::temp_directory_path() /
            ("filesystem_case_study_" + std::to_string(timestamp));

        fs::create_directories(root);

        RepositoryWorkspace workspace(root);

        workspace.createFile(
            "src/main.cpp",
            "#include <iostream>\nint main() { return 0; }\n"
        );

        workspace.createFile(
            "src/config.txt",
            "environment=production\n"
            "log_directory=build/logs\n"
        );

        workspace.createFile(
            "docs/filesystem.md",
            "# Filesystem policy\n"
            "Source files require controlled write access.\n"
        );

        workspace.createFile(
            "build/logs/application.log",
            "2026-10-11 startup complete\n"
        );

        const fs::path config = root / "src" / "config.txt";
        showMetadata(config);

        workspace.protectBuildLogs();

        const auto backup = BackupService::createBackup(root, config);

        std::cout << "\nBackup result: "
                  << std::boolalpha << backup.completed << '\n';
        std::cout << "Backup path: " << backup.backup << '\n';

        workspace.printInventory();

        const fs::path malicious = root / "src" / ".." / ".." / "outside.txt";

        std::cout << "\nPath safety check:\n";
        std::cout << "  Candidate: " << malicious << '\n';
        std::cout << "  Allowed: "
                  << FileSystemPolicy::isSafePath(root, malicious) << '\n';

        try {
            workspace.removeSafely(fs::path("build") / "logs");
            std::cout << "Build logs removed through validated path.\n";
        } catch (const std::exception& error) {
            std::cout << "Safe deletion rejected: "
                      << error.what() << '\n';
        }

        std::error_code cleanupError;
        fs::remove_all(root, cleanupError);

        if (cleanupError) {
            std::cerr << "Cleanup warning: "
                      << cleanupError.message() << '\n';
            return 2;
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Filesystem case study failed: "
                  << error.what() << '\n';
        return 1;
    }
}
