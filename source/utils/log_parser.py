"""
JSON Log Parser and Analysis Utility

Parses structured JSON logs for filtering, aggregation, and reporting.

Usage:
    parser = LogParser("logs/hue_scheduled.log")
    errors = parser.filter_by_level("ERROR")
    stats = parser.get_statistics()
    parser.print_report()
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict, Counter


class LogParser:
    """Parse and analyze structured JSON logs."""

    def __init__(self, log_file: str):
        """
        Initialize parser.

        Args:
            log_file: Path to log file containing JSON-formatted logs
        """
        self.log_file = Path(log_file)
        self.entries: List[Dict[str, Any]] = []
        self._load_logs()

    def _load_logs(self) -> None:
        """Load and parse all log entries from file."""
        if not self.log_file.exists():
            print(f"Error: Log file not found: {self.log_file}", file=sys.stderr)
            return

        with open(self.log_file) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    self.entries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON at line {line_num}: {e}", file=sys.stderr)

    def filter_by_level(self, level: str) -> List[Dict[str, Any]]:
        """Filter entries by log level."""
        return [e for e in self.entries if e.get("level") == level]

    def filter_by_component(self, component: str) -> List[Dict[str, Any]]:
        """Filter entries by component."""
        return [e for e in self.entries if e.get("component") == component]

    def filter_by_message(self, text: str) -> List[Dict[str, Any]]:
        """Filter entries by message text (case-insensitive)."""
        text_lower = text.lower()
        return [e for e in self.entries if text_lower in e.get("message", "").lower()]

    def filter_by_time_range(self, start: str, end: str) -> List[Dict[str, Any]]:
        """Filter entries by timestamp range (ISO 8601 format)."""
        result = []
        for e in self.entries:
            ts = e.get("timestamp", "")
            if start <= ts < end:
                result.append(e)
        return result

    def filter_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Filter entries by status field."""
        return [e for e in self.entries if e.get("status") == status]

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from all log entries."""
        if not self.entries:
            return {}

        stats = {
            "total_entries": len(self.entries),
            "time_range": {
                "start": self.entries[0].get("timestamp"),
                "end": self.entries[-1].get("timestamp"),
            },
            "levels": Counter(e.get("level") for e in self.entries),
            "components": Counter(e.get("component") for e in self.entries),
        }

        # Calculate cycle statistics
        cycles = [e for e in self.entries if e.get("message", "").startswith("Collection cycle")]
        successful_cycles = [e for e in cycles if e.get("status") == "success"]
        failed_cycles = [e for e in cycles if e.get("status") == "failure"]

        stats["cycles"] = {
            "total": len(cycles),
            "successful": len(successful_cycles),
            "failed": len(failed_cycles),
            "success_rate": (len(successful_cycles) / len(cycles) * 100) if cycles else 0,
        }

        # Calculate timing statistics
        durations = [e.get("duration_ms") for e in self.entries if isinstance(e.get("duration_ms"), (int, float))]
        total_durations = [e.get("total_cycle_ms") for e in self.entries if isinstance(e.get("total_cycle_ms"), (int, float))]

        if durations:
            stats["timing"] = {
                "avg_operation_ms": sum(durations) / len(durations),  # type: ignore
                "min_operation_ms": min(durations),  # type: ignore
                "max_operation_ms": max(durations),  # type: ignore
            }

        if total_durations:
            stats["cycle_timing"] = {
                "avg_cycle_ms": sum(total_durations) / len(total_durations),  # type: ignore
                "min_cycle_ms": min(total_durations),  # type: ignore
                "max_cycle_ms": max(total_durations),  # type: ignore
            }

        # Calculate data statistics
        total_readings = sum(e.get("readings_count", 0) for e in self.entries)
        total_duplicates = sum(e.get("duplicates", 0) for e in self.entries)
        stats["data"] = {
            "total_readings": total_readings,
            "total_duplicates": total_duplicates,
        }

        # Calculate error statistics
        errors = self.filter_by_level("ERROR")
        error_codes = Counter(e.get("error_code") for e in errors)
        stats["errors"] = {
            "total": len(errors),
            "by_code": dict(error_codes),
        }

        # Calculate warning statistics
        warnings = self.filter_by_level("WARNING")
        warning_reasons = Counter(e.get("reason") for e in warnings if e.get("reason"))
        warning_messages = Counter(e.get("message") for e in warnings)
        stats["warnings"] = {
            "total": len(warnings),
            "by_reason": dict(warning_reasons),
            "by_message": dict(warning_messages),
        }

        return stats

    def print_report(self) -> None:
        """Print human-readable report."""
        if not self.entries:
            print("No log entries found")
            return

        stats = self.get_statistics()

        print("=" * 80)
        print("LOG ANALYSIS REPORT")
        print("=" * 80)
        print()

        # Time range
        print(f"Time Range: {stats['time_range']['start']} to {stats['time_range']['end']}")
        print()

        # Cycle statistics
        cycles = stats.get("cycles", {})
        print("COLLECTION CYCLES")
        print(f"  Total:       {cycles.get('total', 0)}")
        print(f"  Successful:  {cycles.get('successful', 0)}")
        print(f"  Failed:      {cycles.get('failed', 0)}")
        print(f"  Success Rate: {cycles.get('success_rate', 0):.1f}%")
        print()

        # Timing statistics
        timing = stats.get("timing", {})
        if timing:
            print("OPERATION TIMING")
            print(f"  Average:  {timing.get('avg_operation_ms', 0):.1f}ms")
            print(f"  Min:      {timing.get('min_operation_ms', 0):.1f}ms")
            print(f"  Max:      {timing.get('max_operation_ms', 0):.1f}ms")
            print()

        cycle_timing = stats.get("cycle_timing", {})
        if cycle_timing:
            print("CYCLE TIMING")
            print(f"  Average:  {cycle_timing.get('avg_cycle_ms', 0):.1f}ms")
            print(f"  Min:      {cycle_timing.get('min_cycle_ms', 0):.1f}ms")
            print(f"  Max:      {cycle_timing.get('max_cycle_ms', 0):.1f}ms")
            print()

        # Data statistics
        data = stats.get("data", {})
        print("DATA COLLECTION")
        print(f"  Total Readings:  {data.get('total_readings', 0)}")
        print(f"  Duplicates:      {data.get('total_duplicates', 0)}")
        print()

        # Error statistics
        errors = stats.get("errors", {})
        print("ERRORS")
        print(f"  Total Errors:    {errors.get('total', 0)}")
        if errors.get("by_code"):
            print("  By Code:")
            for code, count in errors.get("by_code", {}).items():
                print(f"    {code}: {count}")
        print()

        # Warning statistics
        warnings = stats.get("warnings", {})
        print("WARNINGS")
        print(f"  Total Warnings:  {warnings.get('total', 0)}")
        if warnings.get("by_reason"):
            print("  By Reason:")
            for reason, count in sorted(warnings.get("by_reason", {}).items(), key=lambda x: -x[1]):
                print(f"    {reason}: {count}")
        print()

        # Log level breakdown
        levels = stats.get("levels", {})
        print("LOG LEVELS")
        for level in ["INFO", "SUCCESS", "WARNING", "ERROR", "DEBUG"]:
            count = levels.get(level, 0)
            if count > 0:
                print(f"  {level:7s}: {count}")
        print()

        # Pass/Fail criteria for testing
        print("TEST PASS/FAIL CRITERIA")
        success_rate = cycles.get('success_rate', 0)
        print(f"  Success Rate >= 98%: {'✓ PASS' if success_rate >= 98 else '✗ FAIL'} ({success_rate:.1f}%)")

        error_count = errors.get("total", 0)
        max_errors = max(1, cycles.get("total", 1) * 0.02)  # 2% of cycles
        print(f"  Error Count <= 2%:  {'✓ PASS' if error_count <= max_errors else '✗ FAIL'} ({error_count}/{max_errors:.0f})")

        print()
        print("=" * 80)


# Example usage for testing
if __name__ == "__main__":
    import sys
    
    # Support multiple log files as command-line arguments
    if len(sys.argv) > 1:
        # Real usage: python log_parser.py logs/hue_scheduled.log logs/amazon_scheduled.log
        parsers = []
        all_entries = []
        
        for log_file_path in sys.argv[1:]:
            if Path(log_file_path).exists():
                parser = LogParser(log_file_path)
                parsers.append(parser)
                all_entries.extend(parser.entries)
        
        if not all_entries:
            print("No log entries found in specified files")
            sys.exit(0)
        
        # Create a combined parser with all entries
        combined_parser = LogParser.__new__(LogParser)
        combined_parser.log_file = Path("combined")
        combined_parser.entries = sorted(all_entries, key=lambda x: x.get('timestamp', ''))
        combined_parser.print_report()
    else:
        # Test mode: Create sample log entries for testing
        log_file = Path("/tmp/test_logs.jsonl")

        sample_logs = [
            '{"timestamp":"2025-11-21T06:15:00.000Z","level":"INFO","component":"runner_script","message":"Starting Hue collection cycle","cycle_id":"hue-1"}',
            '{"timestamp":"2025-11-21T06:15:01.234Z","level":"INFO","component":"hue_collector","message":"Connected to Hue Bridge","bridge_ip":"192.168.1.105","duration_ms":1234}',
            '{"timestamp":"2025-11-21T06:15:02.500Z","level":"INFO","component":"hue_collector","message":"Discovered temperature sensors","sensor_count":26,"temperature_sensors":2,"device_ids":["Utility","Hall"],"duration_ms":200}',
            '{"timestamp":"2025-11-21T06:15:03.800Z","level":"SUCCESS","component":"hue_collector","message":"Collection completed successfully","readings_count":2,"duration_ms":800,"total_cycle_ms":3800,"status":"success"}',
            '{"timestamp":"2025-11-21T06:15:04.200Z","level":"INFO","component":"storage_manager","message":"Readings stored","readings_count":2,"duplicates":0,"errors":0,"duration_ms":400}',
            '{"timestamp":"2025-11-21T06:15:05.000Z","level":"INFO","component":"runner_script","message":"Collection cycle complete","cycle_id":"hue-1","status":"success","total_duration_ms":5000,"readings_stored":2}',
        ]

        with open(log_file, "w") as f:
            f.write("\n".join(sample_logs))

        # Test parser
        parser = LogParser(str(log_file))
        print(f"Loaded {len(parser.entries)} log entries")
        print()

        # Test filtering
        errors = parser.filter_by_level("ERROR")
        print(f"Errors: {len(errors)}")

        hue_logs = parser.filter_by_component("hue_collector")
        print(f"Hue collector logs: {len(hue_logs)}")
        print()

        # Print report
        parser.print_report()
