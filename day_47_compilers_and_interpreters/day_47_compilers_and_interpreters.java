import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/*
 * Enterprise scenario: executing deployment and release policies.
 *
 * The policy engine distinguishes compilation from execution. Compilation
 * validates an expression and produces immutable bytecode instructions.
 * Execution evaluates that bytecode against a deployment-specific context.
 *
 * Requires Java 17 or later:
 *     javac RuntimePolicyEngine.java
 *     java RuntimePolicyEngine
 */
public final class RuntimePolicyEngine {

    private RuntimePolicyEngine() {}

    public sealed interface Value permits NumberValue, BooleanValue {}

    public record NumberValue(double value) implements Value {
        public NumberValue {
            if (!Double.isFinite(value)) {
                throw new IllegalArgumentException(
                    "Numeric values must be finite"
                );
            }
        }
    }

    public record BooleanValue(boolean value) implements Value {}

    public enum Operator {
        ADD, SUBTRACT, MULTIPLY, DIVIDE, LESS, LESS_EQUAL, EQUAL
    }

    public sealed interface Expression
        permits Literal, Reference, BinaryExpression {}

    public record Literal(Value value) implements Expression {
        public Literal {
            Objects.requireNonNull(value, "value");
        }
    }

    public record Reference(String name) implements Expression {
        public Reference {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Reference name cannot be blank"
                );
            }
        }
    }

    public record BinaryExpression(
        Operator operator,
        Expression left,
        Expression right
    ) implements Expression {
        public BinaryExpression {
            Objects.requireNonNull(operator, "operator");
            Objects.requireNonNull(left, "left");
            Objects.requireNonNull(right, "right");
        }
    }

    public enum Opcode {
        CONSTANT, LOAD, ADD, SUBTRACT, MULTIPLY, DIVIDE,
        LESS, LESS_EQUAL, EQUAL, HALT
    }

    public record Instruction(Opcode opcode, Object operand) {
        public Instruction {
            Objects.requireNonNull(opcode, "opcode");
        }
    }

    public static final class PolicyCompileException
        extends RuntimeException {
        public PolicyCompileException(String message) {
            super(message);
        }
    }

    public static final class PolicyExecutionException
        extends RuntimeException {
        public PolicyExecutionException(String message) {
            super(message);
        }
    }

    /*
     * The compiler accepts an explicit allowlist of context variables.
     * Unknown names fail before deployment evaluation starts.
     */
    public static final class Compiler {
        private final java.util.Set<String> allowedVariables;

        public Compiler(java.util.Set<String> allowedVariables) {
            this.allowedVariables = java.util.Set.copyOf(allowedVariables);
        }

        public List<Instruction> compile(Expression expression) {
            List<Instruction> instructions = new ArrayList<>();
            emit(expression, instructions);
            instructions.add(new Instruction(Opcode.HALT, null));
            return List.copyOf(instructions);
        }

        private void emit(
            Expression expression,
            List<Instruction> instructions
        ) {
            if (expression instanceof Literal literal) {
                instructions.add(
                    new Instruction(Opcode.CONSTANT, literal.value())
                );
                return;
            }

            if (expression instanceof Reference reference) {
                if (!allowedVariables.contains(reference.name())) {
                    throw new PolicyCompileException(
                        "Unknown policy variable: " + reference.name()
                    );
                }
                instructions.add(
                    new Instruction(Opcode.LOAD, reference.name())
                );
                return;
            }

            if (expression instanceof BinaryExpression binary) {
                emit(binary.left(), instructions);
                emit(binary.right(), instructions);

                Opcode opcode = switch (binary.operator()) {
                    case ADD -> Opcode.ADD;
                    case SUBTRACT -> Opcode.SUBTRACT;
                    case MULTIPLY -> Opcode.MULTIPLY;
                    case DIVIDE -> Opcode.DIVIDE;
                    case LESS -> Opcode.LESS;
                    case LESS_EQUAL -> Opcode.LESS_EQUAL;
                    case EQUAL -> Opcode.EQUAL;
                };

                instructions.add(new Instruction(opcode, null));
                return;
            }

            throw new PolicyCompileException("Unsupported expression");
        }
    }

    /*
     * Each execution receives its own context and operand stack. The
     * immutable instruction list can be reused safely across deployments.
     */
    public static final class VirtualMachine {
        private final List<Instruction> instructions;
        private final Map<String, Value> context;
        private final Deque<Value> stack = new ArrayDeque<>();
        private final int instructionLimit;

        public VirtualMachine(
            List<Instruction> instructions,
            Map<String, Value> context,
            int instructionLimit
        ) {
            this.instructions = List.copyOf(instructions);
            this.context = Map.copyOf(context);

            if (instructionLimit <= 0) {
                throw new IllegalArgumentException(
                    "Instruction limit must be positive"
                );
            }
            this.instructionLimit = instructionLimit;

            if (this.instructions.isEmpty()
                || this.instructions.get(this.instructions.size() - 1)
                    .opcode() != Opcode.HALT) {
                throw new PolicyCompileException(
                    "Program must terminate with HALT"
                );
            }
        }

        public Value execute() {
            int ip = 0;
            int executed = 0;

            while (ip < instructions.size()) {
                if (++executed > instructionLimit) {
                    throw new PolicyExecutionException(
                        "Instruction limit exceeded"
                    );
                }

                Instruction instruction = instructions.get(ip++);

                switch (instruction.opcode()) {
                    case CONSTANT -> {
                        if (!(instruction.operand() instanceof Value value)) {
                            throw new PolicyExecutionException(
                                "Invalid constant operand"
                            );
                        }
                        stack.push(value);
                    }

                    case LOAD -> {
                        String name = (String) instruction.operand();
                        Value value = context.get(name);
                        if (value == null) {
                            throw new PolicyExecutionException(
                                "Missing runtime variable: " + name
                            );
                        }
                        stack.push(value);
                    }

                    case ADD -> arithmetic((a, b) -> a + b);
                    case SUBTRACT -> arithmetic((a, b) -> a - b);
                    case MULTIPLY -> arithmetic((a, b) -> a * b);

                    case DIVIDE -> arithmetic((a, b) -> {
                        if (b == 0.0) {
                            throw new PolicyExecutionException(
                                "Division by zero"
                            );
                        }
                        return a / b;
                    });

                    case LESS -> comparison((a, b) -> a < b);
                    case LESS_EQUAL -> comparison((a, b) -> a <= b);

                    case EQUAL -> {
                        Value right = pop();
                        Value left = pop();
                        stack.push(new BooleanValue(left.equals(right)));
                    }

                    case HALT -> {
                        if (stack.size() != 1) {
                            throw new PolicyExecutionException(
                                "Expected exactly one result, found "
                                    + stack.size()
                            );
                        }
                        return stack.pop();
                    }
                }
            }

            throw new PolicyExecutionException(
                "Execution ended without HALT"
            );
        }

        private Value pop() {
            if (stack.isEmpty()) {
                throw new PolicyExecutionException(
                    "Operand stack underflow"
                );
            }
            return stack.pop();
        }

        private double asNumber(Value value) {
            if (!(value instanceof NumberValue number)) {
                throw new PolicyExecutionException(
                    "Numeric operator received Boolean"
                );
            }
            return number.value();
        }

        private void arithmetic(
            java.util.function.DoubleBinaryOperator operation
        ) {
            double right = asNumber(pop());
            double left = asNumber(pop());
            double result = operation.applyAsDouble(left, right);

            if (!Double.isFinite(result)) {
                throw new PolicyExecutionException(
                    "Arithmetic produced a non-finite result"
                );
            }
            stack.push(new NumberValue(result));
        }

        private void comparison(
            java.util.function.BiPredicate<Double, Double> predicate
        ) {
            double right = asNumber(pop());
            double left = asNumber(pop());
            stack.push(new BooleanValue(predicate.test(left, right)));
        }
    }

    private static Expression number(double value) {
        return new Literal(new NumberValue(value));
    }

    private static Expression variable(String name) {
        return new Reference(name);
    }

    private static Expression binary(
        Operator operator,
        Expression left,
        Expression right
    ) {
        return new BinaryExpression(operator, left, right);
    }

    private static Map<String, Value> context(
        double failedChecks,
        double criticalFindings,
        double deploymentWindowHours
    ) {
        Map<String, Value> values = new HashMap<>();
        values.put("failed_checks", new NumberValue(failedChecks));
        values.put("critical_findings", new NumberValue(criticalFindings));
        values.put(
            "deployment_window_hours",
            new NumberValue(deploymentWindowHours)
        );
        return Map.copyOf(values);
    }

    private static boolean evaluate(
        List<Instruction> program,
        Map<String, Value> context
    ) {
        Value result = new VirtualMachine(program, context, 1000).execute();

        if (!(result instanceof BooleanValue decision)) {
            throw new PolicyExecutionException(
                "Deployment policy must return Boolean"
            );
        }

        return decision.value();
    }

    public static void main(String[] args) {
        var allowed = java.util.Set.of(
            "failed_checks",
            "critical_findings",
            "deployment_window_hours"
        );

        Compiler compiler = new Compiler(allowed);

        /*
         * Release is eligible when there are no critical findings and the
         * deployment window is at least two hours long.
         */
        Expression releasePolicy = binary(
            Operator.EQUAL,
            binary(
                Operator.ADD,
                variable("critical_findings"),
                number(0)
            ),
            number(0)
        );

        Expression windowPolicy = binary(
            Operator.LESS_EQUAL,
            number(2),
            variable("deployment_window_hours")
        );

        // Combining two Boolean conditions is deliberately handled by a
        // service-level policy composition, not by an implicit truthy rule.
        List<Instruction> noCriticalProgram = compiler.compile(releasePolicy);
        List<Instruction> windowProgram = compiler.compile(windowPolicy);

        Map<String, Value> productionContext = context(0, 0, 3);
        boolean noCritical = evaluate(noCriticalProgram, productionContext);
        boolean adequateWindow = evaluate(windowProgram, productionContext);
        boolean releaseEligible = noCritical && adequateWindow;

        System.out.println("No critical findings: " + noCritical);
        System.out.println("Deployment window acceptable: " + adequateWindow);
        System.out.println("Release eligible: " + releaseEligible);

        Map<String, Value> blockedContext = context(1, 2, 1);
        boolean blocked = !evaluate(noCriticalProgram, blockedContext)
            || !evaluate(windowProgram, blockedContext);
        System.out.println("Unsafe release blocked: " + blocked);

        try {
            compiler.compile(variable("unapproved_policy_variable"));
        } catch (PolicyCompileException exception) {
            System.out.println(
                "Compile-time policy rejection: " + exception.getMessage()
            );
        }

        try {
            Expression division = binary(
                Operator.DIVIDE,
                number(10),
                number(0)
            );
            List<Instruction> divisionProgram = compiler.compile(division);
            new VirtualMachine(divisionProgram, Map.of(), 100).execute();
        } catch (PolicyExecutionException exception) {
            System.out.println(
                "Runtime policy failure: " + exception.getMessage()
            );
        }
    }
}
