from __future__ import annotations

from datetime import datetime, timezone
import argparse


DOTNET_EPOCH = datetime(1, 1, 1, tzinfo=timezone.utc)


def datetime_to_dotnet_ticks(dt: datetime) -> int:
	"""
	Convert a datetime to .NET ticks.

	.NET tick: 100-nanosecond interval since 0001-01-01 00:00:00 UTC.
	"""
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=timezone.utc)
	else:
		dt = dt.astimezone(timezone.utc)

	delta = dt - DOTNET_EPOCH
	return (
		(delta.days * 24 * 60 * 60 + delta.seconds) * 10_000_000
		+ delta.microseconds * 10
	)


def parse_datetime(text: str, fmt: str, as_utc: bool) -> datetime:
	"""
	Parse datetime from either custom format or ISO-8601.
	"""
	if fmt.lower() == "iso":
		dt = datetime.fromisoformat(text)
	else:
		dt = datetime.strptime(text, fmt)

	if as_utc:
		if dt.tzinfo is None:
			dt = dt.replace(tzinfo=timezone.utc)
		else:
			dt = dt.astimezone(timezone.utc)
	else:
		if dt.tzinfo is None:
			local_tz = datetime.now().astimezone().tzinfo
			dt = dt.replace(tzinfo=local_tz)

	return dt


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Convert date string to .NET ticks."
	)
	parser.add_argument(
		"date",
		help="Date string, for example '2026-04-06 12:34:56' or ISO format",
	)
	parser.add_argument(
		"-f",
		"--format",
		default="%Y-%m-%d %H:%M:%S",
		help="Input date format, or use 'iso' for datetime.fromisoformat",
	)
	parser.add_argument(
		"--utc",
		action="store_true",
		help="Treat input as UTC. Without this, naive datetime is treated as local time.",
	)

	args = parser.parse_args()
	dt = parse_datetime(args.date, args.format, args.utc)
	ticks = datetime_to_dotnet_ticks(dt)
	print(ticks)


if __name__ == "__main__":
	main()
