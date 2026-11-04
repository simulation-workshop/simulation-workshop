"""Tiny example used by the include demo."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def main() -> None:
    print(add(2, 3))


if __name__ == "__main__":
    main()
