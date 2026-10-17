#include <cmath>
#include <cstddef>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>

/*
 * Case study: a bytecode execution engine for a repository build-policy DSL.
 *
 * A build-policy expression can evaluate arithmetic and Boolean conditions
 * such as:
 *
 *     risk = changed_files * 2 + critical_findings * 10
 *     eligible = risk < 20
 *
 * The compiler converts expression trees into stack-machine instructions.
 * The VM evaluates the instructions using typed values, explicit failure
 * handling, and an execution budget.
 *
 * Compile:
 *     g++ -std=c++17 -Wall -Wextra -pedantic runtime_engine.cpp -o runtime_engine
 */

using Value = std::variant<double, bool>;

enum class Op {
    PushNumber,
    PushBoolean,
    Load,
    Store,
    Add,
    Subtract,
    Multiply,
    Divide,
    Less,
    LessEqual,
    Equal,
    JumpIfFalse,
    Jump,
    Halt
};

struct Instruction {
    Op op;
    std::variant<std::monostate, double, bool, std::string, std::size_t> arg;
};

class CompileError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class RuntimeError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

struct Expr {
    virtual ~Expr() = default;
};

struct NumberExpr final : Expr {
    double value;
    explicit NumberExpr(double value) : value(value) {}
};

struct BooleanExpr final : Expr {
    bool value;
    explicit BooleanExpr(bool value) : value(value) {}
};

struct VariableExpr final : Expr {
    std::string name;
    explicit VariableExpr(std::string name) : name(std::move(name)) {}
};

struct BinaryExpr final : Expr {
    Op operation;
    std::unique_ptr<Expr> left;
    std::unique_ptr<Expr> right;

    BinaryExpr(
        Op operation,
        std::unique_ptr<Expr> left,
        std::unique_ptr<Expr> right
    )
        : operation(operation),
          left(std::move(left)),
          right(std::move(right)) {}
};

/*
 * A small expression AST keeps the compiler independent of the runtime.
 * Ownership is explicit: each binary node owns its child expressions.
 */
class Compiler {
public:
    std::vector<Instruction> compile(const Expr& expression) {
        code_.clear();
        emitExpression(expression);
        emit(Op::Halt);
        return code_;
    }

private:
    std::vector<Instruction> code_;

    void emit(Op op) {
        code_.push_back({op, std::monostate{}});
    }

    template <typename T>
    void emit(Op op, T argument) {
        code_.push_back({op, std::move(argument)});
    }

    void emitExpression(const Expr& expression) {
        if (const auto* number = dynamic_cast<const NumberExpr*>(&expression)) {
            emit(Op::PushNumber, number->value);
            return;
        }

        if (const auto* boolean = dynamic_cast<const BooleanExpr*>(&expression)) {
            emit(Op::PushBoolean, boolean->value);
            return;
        }

        if (const auto* variable = dynamic_cast<const VariableExpr*>(&expression)) {
            emit(Op::Load, variable->name);
            return;
        }

        if (const auto* binary = dynamic_cast<const BinaryExpr*>(&expression)) {
            emitExpression(*binary->left);
            emitExpression(*binary->right);
            emit(binary->operation);
            return;
        }

        throw CompileError("Unsupported expression node");
    }
};

class VirtualMachine {
public:
    explicit VirtualMachine(
        std::vector<Instruction> instructions,
        std::size_t instruction_budget = 10000
    )
        : code_(std::move(instructions)),
          budget_(instruction_budget) {
        verify();
    }

    void setVariable(const std::string& name, Value value) {
        environment_[name] = std::move(value);
    }

    Value run() {
        while (ip_ < code_.size()) {
            if (budget_ == 0) {
                throw RuntimeError("Instruction budget exhausted");
            }
            --budget_;

            const Instruction& instruction = code_[ip_++];

            switch (instruction.op) {
                case Op::PushNumber:
                    stack_.emplace_back(std::get<double>(instruction.arg));
                    break;

                case Op::PushBoolean:
                    stack_.emplace_back(std::get<bool>(instruction.arg));
                    break;

                case Op::Load: {
                    const std::string& name =
                        std::get<std::string>(instruction.arg);
                    auto found = environment_.find(name);
                    if (found == environment_.end()) {
                        throw RuntimeError("Undefined variable: " + name);
                    }
                    stack_.push_back(found->second);
                    break;
                }

                case Op::Store: {
                    const std::string& name =
                        std::get<std::string>(instruction.arg);
                    environment_[name] = pop();
                    break;
                }

                case Op::Add:
                    numericBinary([](double a, double b) { return a + b; });
                    break;

                case Op::Subtract:
                    numericBinary([](double a, double b) { return a - b; });
                    break;

                case Op::Multiply:
                    numericBinary([](double a, double b) { return a * b; });
                    break;

                case Op::Divide:
                    numericBinary([](double a, double b) {
                        if (b == 0.0) {
                            throw RuntimeError("Division by zero");
                        }
                        return a / b;
                    });
                    break;

                case Op::Less:
                    compare([](double a, double b) { return a < b; });
                    break;

                case Op::LessEqual:
                    compare([](double a, double b) { return a <= b; });
                    break;

                case Op::Equal: {
                    Value right = pop();
                    Value left = pop();
                    // variant equality requires matching alternatives.
                    stack_.emplace_back(left == right);
                    break;
                }

                case Op::JumpIfFalse: {
                    Value condition = pop();
                    if (!std::holds_alternative<bool>(condition)) {
                        throw RuntimeError("Conditional jump requires Boolean");
                    }
                    if (!std::get<bool>(condition)) {
                        ip_ = std::get<std::size_t>(instruction.arg);
                    }
                    break;
                }

                case Op::Jump:
                    ip_ = std::get<std::size_t>(instruction.arg);
                    break;

                case Op::Halt:
                    if (stack_.empty()) {
                        throw RuntimeError("No result on operand stack");
                    }
                    return stack_.back();
            }
        }

        throw RuntimeError("Program terminated without HALT");
    }

private:
    std::vector<Instruction> code_;
    std::vector<Value> stack_;
    std::unordered_map<std::string, Value> environment_;
    std::size_t ip_ = 0;
    std::size_t budget_;

    void verify() const {
        if (code_.empty() || code_.back().op != Op::Halt) {
            throw CompileError("Bytecode must end with HALT");
        }

        for (const auto& instruction : code_) {
            if (instruction.op == Op::Jump ||
                instruction.op == Op::JumpIfFalse) {
                const auto* target =
                    std::get_if<std::size_t>(&instruction.arg);
                if (target == nullptr || *target >= code_.size()) {
                    throw CompileError("Invalid jump target");
                }
            }
        }
    }

    Value pop() {
        if (stack_.empty()) {
            throw RuntimeError("Operand stack underflow");
        }
        Value result = stack_.back();
        stack_.pop_back();
        return result;
    }

    static double number(const Value& value, const std::string& operation) {
        if (!std::holds_alternative<double>(value)) {
            throw RuntimeError(
                "Operator " + operation + " requires numeric operands"
            );
        }

        double result = std::get<double>(value);
        if (!std::isfinite(result)) {
            throw RuntimeError("Non-finite numeric value");
        }
        return result;
    }

    template <typename Function>
    void numericBinary(Function operation) {
        const double right = number(pop(), "arithmetic");
        const double left = number(pop(), "arithmetic");
        const double result = operation(left, right);

        if (!std::isfinite(result)) {
            throw RuntimeError("Arithmetic produced a non-finite result");
        }

        stack_.emplace_back(result);
    }

    template <typename Predicate>
    void compare(Predicate predicate) {
        const double right = number(pop(), "comparison");
        const double left = number(pop(), "comparison");
        stack_.emplace_back(predicate(left, right));
    }
};

std::string display(const Value& value) {
    if (std::holds_alternative<bool>(value)) {
        return std::get<bool>(value) ? "true" : "false";
    }

    double number = std::get<double>(value);
    std::ostringstream stream;
    stream << std::setprecision(12) << number;
    return stream.str();
}

int main() {
    try {
        /*
         * Build-policy expression:
         *   risk = changed_files * 2 + critical_findings * 10
         *   eligible = risk < 20
         *
         * The final comparison is compiled directly into bytecode. The
         * environment supplies values from a repository analysis service.
         */
        auto riskExpression = std::make_unique<BinaryExpr>(
            Op::Add,
            std::make_unique<BinaryExpr>(
                Op::Multiply,
                std::make_unique<VariableExpr>("changed_files"),
                std::make_unique<NumberExpr>(2.0)
            ),
            std::make_unique<BinaryExpr>(
                Op::Multiply,
                std::make_unique<VariableExpr>("critical_findings"),
                std::make_unique<NumberExpr>(10.0)
            )
        );

        Compiler compiler;
        auto riskCode = compiler.compile(*riskExpression);
        VirtualMachine riskVM(std::move(riskCode));
        riskVM.setVariable("changed_files", 4.0);
        riskVM.setVariable("critical_findings", 1.0);

        const Value risk = riskVM.run();
        std::cout << "Pull request risk score: " << display(risk) << '\n';

        auto eligibilityExpression = std::make_unique<BinaryExpr>(
            Op::Less,
            std::make_unique<VariableExpr>("risk"),
            std::make_unique<NumberExpr>(20.0)
        );

        auto eligibilityCode = compiler.compile(*eligibilityExpression);
        VirtualMachine eligibilityVM(std::move(eligibilityCode));
        eligibilityVM.setVariable("risk", risk);

        const Value eligible = eligibilityVM.run();
        std::cout << "Eligible under risk threshold: "
                  << display(eligible) << '\n';

        // Boundary case: exactly 20 is not below a strict threshold.
        eligibilityVM.setVariable("risk", 20.0);
        auto boundaryCode = compiler.compile(*eligibilityExpression);
        VirtualMachine boundaryVM(std::move(boundaryCode));
        boundaryVM.setVariable("risk", 20.0);
        std::cout << "Risk score 20 eligible: "
                  << display(boundaryVM.run()) << '\n';

        // Runtime errors are reported rather than silently converted.
        try {
            auto invalid = std::make_unique<BinaryExpr>(
                Op::Divide,
                std::make_unique<NumberExpr>(10.0),
                std::make_unique<NumberExpr>(0.0)
            );
            auto invalidCode = compiler.compile(*invalid);
            VirtualMachine invalidVM(std::move(invalidCode));
            (void)invalidVM.run();
        } catch (const RuntimeError& error) {
            std::cout << "Expected runtime failure: "
                      << error.what() << '\n';
        }

        // Undefined runtime bindings are rejected by LOAD.
        try {
            VariableExpr missing("unconfigured_policy_value");
            auto missingCode = compiler.compile(missing);
            VirtualMachine missingVM(std::move(missingCode));
            (void)missingVM.run();
        } catch (const RuntimeError& error) {
            std::cout << "Expected binding failure: "
                      << error.what() << '\n';
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal engine error: " << error.what() << '\n';
        return 1;
    }
}
