from services.coordinator_service import (
    generate_health_report,
)

if __name__ == "__main__":
    report = generate_health_report(1)

    print("\n=== FINAL REPORT ===\n")

    print(report)
