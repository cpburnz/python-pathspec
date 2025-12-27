"""
This script generates the markdown tables for the benchmark run.
"""

import argparse
import dataclasses
import json
import pathlib
import re
import sys


def output_md_tables(in_file: pathlib.Path) -> None:
	"""
	Output the markdown tables for the benchmark.
	"""
	run_info = json.loads(in_file.read_text())

	python_ver = run_info['machine_info']['python_version']
	impl_ver = run_info['machine_info']['python_implementation_version']
	python = "{python} {version}".format(
		python=run_info['machine_info']['python_implementation'],
		version=python_ver,
	)
	if impl_ver != python_ver:
		python += f" ({impl_ver})"

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
	print(f"{python} on {machine}")
	print("----------")
	print()
	for table_key, table_rows in table_to_times.items():
		print(f"{table_key.method}: {table_key.file_count} files ")
		print()
		print("| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |")
		print("| --: | --: | --: | --: | --: | --: |")

		for line_count, backend_ops in sorted(table_rows.items()):
			sm_ops = backend_ops['sm']
			hs_ops = backend_ops.get('hs')
			re2_ops = backend_ops.get('re2')
			print("| " + " | ".join([
				str(line_count),
				format(sm_ops, '.1f'),
				format(hs_ops, '.1f') if hs_ops else "-",
				format(hs_ops / sm_ops, '.2f') if hs_ops else "-",
				format(re2_ops, '.1f') if re2_ops else "-",
				format(re2_ops / sm_ops, '.2f') if re2_ops else "-",
			]) + " |")

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

	output_md_tables(args.i)

	return 0


@dataclasses.dataclass(frozen=True)
class TableKey(object):
	file_count: str
	method: str


if __name__ == '__main__':
	sys.exit(main())
