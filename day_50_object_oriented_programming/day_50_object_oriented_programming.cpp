#include <algorithm>
#include <iomanip>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

class ValidationError : public std::runtime_error {
public:
    explicit ValidationError(const std::string& message)
        : std::runtime_error(message) {}
};

class Shape {
public:
    virtual ~Shape() = default;

    virtual double area() const = 0;
    virtual double perimeter() const = 0;
    virtual std::string name() const = 0;

    virtual void scale(double factor) = 0;
};

class Rectangle final : public Shape {
private:
    double width_;
    double height_;

public:
    Rectangle(double width, double height)
        : width_(width), height_(height) {
        validate();
    }

    double area() const override {
        return width_ * height_;
    }

    double perimeter() const override {
        return 2.0 * (width_ + height_);
    }

    std::string name() const override {
        return "Rectangle";
    }

    void scale(double factor) override {
        if (factor <= 0.0) {
            throw ValidationError("Scale factor must be positive.");
        }

        width_ *= factor;
        height_ *= factor;
    }

private:
    void validate() const {
        if (width_ <= 0.0 || height_ <= 0.0) {
            throw ValidationError("Rectangle dimensions must be positive.");
        }
    }
};

class Circle final : public Shape {
private:
    double radius_;

public:
    explicit Circle(double radius)
        : radius_(radius) {
        if (radius_ <= 0.0) {
            throw ValidationError("Circle radius must be positive.");
        }
    }

    double area() const override {
        constexpr double pi = 3.14159265358979323846;
        return pi * radius_ * radius_;
    }

    double perimeter() const override {
        constexpr double pi = 3.14159265358979323846;
        return 2.0 * pi * radius_;
    }

    std::string name() const override {
        return "Circle";
    }

    void scale(double factor) override {
        if (factor <= 0.0) {
            throw ValidationError("Scale factor must be positive.");
        }

        radius_ *= factor;
    }
};

class ShapeRepository {
private:
    std::vector<std::unique_ptr<Shape>> shapes_;

public:
    void add(std::unique_ptr<Shape> shape) {
        if (!shape) {
            throw ValidationError("Cannot store a null shape.");
        }

        shapes_.push_back(std::move(shape));
    }

    double totalArea() const {
        double total = 0.0;

        for (const auto& shape : shapes_) {
            total += shape->area();
        }

        return total;
    }

    void scaleAll(double factor) {
        for (auto& shape : shapes_) {
            shape->scale(factor);
        }
    }

    void printReport() const {
        std::cout << std::fixed << std::setprecision(2);

        for (const auto& shape : shapes_) {
            std::cout
                << shape->name()
                << " | area=" << shape->area()
                << " | perimeter=" << shape->perimeter()
                << '\n';
        }

        std::cout << "Total area: " << totalArea() << '\n';
    }
};

int main() {
    try {
        ShapeRepository repository;

        // unique_ptr provides exclusive ownership and prevents leaks.
        repository.add(std::make_unique<Rectangle>(10.0, 5.0));
        repository.add(std::make_unique<Circle>(4.0));

        std::cout << "Initial geometry report\n";
        repository.printReport();

        // Shape pointers invoke overridden methods through dynamic dispatch.
        repository.scaleAll(2.0);

        std::cout << "\nAfter polymorphic scaling\n";
        repository.printReport();

        try {
            repository.add(std::make_unique<Circle>(-2.0));
        } catch (const ValidationError& error) {
            std::cerr << "Rejected shape: " << error.what() << '\n';
        }

        try {
            repository.scaleAll(0.0);
        } catch (const ValidationError& error) {
            std::cerr << "Rejected operation: " << error.what() << '\n';
        }

        /*
         * Encapsulation keeps dimensions private.
         * Clients can manipulate shapes only through validated behavior.
         * The abstract Shape interface allows the repository to remain
         * independent of concrete shape implementations.
         */
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
