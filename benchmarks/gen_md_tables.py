"""
This script generates the RST tables for the benchmark run.
"""

import argparse
import dataclasses
import json
import pathlib
import re
import sys


def output_rst_tables(in_file: pathlib.Path) -> None:
	"""
	Output the RST tables for the benchmark.
	"""
	run_info = json.loads(in_file.read_text())

	python = "{python} {version}".format(
		python=run_info['machine_info']['python_implementation'],
		version=run_info['machine_info']['python_implementation_version'],
	)
	machine = run_info['machine_info']['cpu']['brand_raw']

	table_to_times: dict[TableKey, dict[int, dict[str, float]]] = {}
	for benchmark in run_info['benchmarks']:
		ops = benchmark['stats']['ops']
		method = benchmark['group'].split(':')[0]
		file_count = re.search('\\b(\\S+) files\\b', benchmark['group']).group(1)
		line_count = int(re.search('\\b(\\S+) lines?\\b', benchmark['group']).group(1))
		backend = re.search('^bench_([a-z0-9]+)_', benchmark['name']).group(1)

		table_key = TableKey(method=method, file_count=file_count)
		table_to_times.setdefault(table_key, {}).setdefault(line_count, {})[backend] = ops

	print()
	for table_key, table_rows in table_to_times.items():
		print(f".. list-table:: {table_key.method}: {table_key.file_count} files using {python} on {machine}")
		print("   :header-rows: 2")
		print("   :align: right")
		print()
		print("   * - Patterns")
		print("     - simple")
		print("     - hyperscan")
		print("     -")
		print("     - re2")
		print("     -")
		print("   * -")
		print("     - ops")
		print("     - ops")
		print("     - x")
		print("     - ops")
		print("     - x")

		for line_count, backend_ops in sorted(table_rows.items()):
			sm_ops = backend_ops['sm']
			hs_ops = backend_ops['hs']
			re2_ops = backend_ops['re2']
			print(f"   * - {line_count}")
			print(f"     - {sm_ops:.1f}")
			print(f"     - {hs_ops:.1f}")
			print(f"     - {hs_ops/sm_ops:.2f}")
			print(f"     - {re2_ops:.1f}")
			print(f"     - {re2_ops/sm_ops:.2f}")

		print()


def main() -> int:
	"""
	Run the script.
	"""
	# Parse command-line arguments.
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('-i', type=pathlib.Path, required=True, help=(
		"The saved benchmark run."
	), metavar="<json>")
	args = parser.parse_args()

	output_rst_tables(args.i)

	return 0


@dataclasses.dataclass(frozen=True)
class TableKey(object):
	file_count: str
	method: str


if __name__ == '__main__':
	sys.exit(main())
