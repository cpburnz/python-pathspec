
These benchmarks compare the native Python `re` module ("simple" backend) with
the optional backends. They were run against the CPython source main branch from
2025-12-27 (commit 00e24b80e092e7d36dc189fd260b2a4e730a6e7f), configured and
compiled. `PathSpec` and `GitIgnoreSpec` are tested using preloaded `.gitignore`
patterns and file paths. File-system speed is not tested.


CPython 3.13.11 on Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz
----------

GitIgnoreSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 163.4 | 91.4 | 0.56 | 87.2 | 0.53 |
| 5 | 64.4 | 74.3 | 1.15 | 87.9 | 1.36 |
| 15 | 24.9 | 67.3 | 2.70 | 84.3 | 3.38 |
| 25 | 17.5 | 31.5 | 1.80 | 82.5 | 4.73 |
| 50 | 9.1 | 21.1 | 2.31 | 82.4 | 9.01 |
| 100 | 4.9 | 32.7 | 6.62 | 77.6 | 15.73 |
| 150 | 3.6 | 30.3 | 8.41 | 73.0 | 20.25 |

PathSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 165.5 | 102.2 | 0.62 | 87.8 | 0.53 |
| 5 | 65.7 | 84.2 | 1.28 | 88.0 | 1.34 |
| 15 | 29.2 | 72.4 | 2.48 | 78.5 | 2.69 |
| 25 | 16.0 | 32.8 | 2.06 | 79.2 | 4.96 |
| 50 | 9.3 | 20.4 | 2.20 | 77.0 | 8.29 |
| 100 | 5.2 | 25.3 | 4.83 | 74.4 | 14.21 |
| 150 | 3.7 | 28.6 | 7.68 | 72.8 | 19.58 |


PyPy 3.11.13 (7.3.20) on Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz
----------

GitIgnoreSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 317.0 | - | - | - | - |
| 5 | 45.0 | - | - | - | - |
| 15 | 14.4 | - | - | - | - |
| 25 | 8.2 | - | - | - | - |
| 50 | 3.9 | - | - | - | - |
| 100 | 1.9 | - | - | - | - |
| 150 | 0.9 | - | - | - | - |

PathSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 321.6 | - | - | - | - |
| 5 | 43.4 | - | - | - | - |
| 15 | 16.9 | - | - | - | - |
| 25 | 8.2 | - | - | - | - |
| 50 | 3.9 | - | - | - | - |
| 100 | 2.1 | - | - | - | - |
| 150 | 1.1 | - | - | - | - |


CPython 3.13.11 on 11th Gen Intel(R) Core(TM) i7-1165G7 @ 2.80GHz
----------

GitIgnoreSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 271.9 | 187.2 | 0.69 | 196.3 | 0.72 |
| 5 | 106.0 | 161.1 | 1.52 | 198.8 | 1.88 |
| 15 | 46.1 | 146.5 | 3.18 | 193.3 | 4.19 |
| 25 | 27.2 | 55.4 | 2.04 | 191.8 | 7.05 |
| 50 | 15.7 | 37.8 | 2.40 | 190.7 | 12.12 |
| 100 | 8.5 | 66.9 | 7.88 | 190.9 | 22.47 |
| 150 | 5.8 | 60.5 | 10.46 | 173.0 | 29.91 |

PathSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 276.2 | 204.6 | 0.74 | 194.9 | 0.71 |
| 5 | 104.7 | 172.0 | 1.64 | 194.1 | 1.85 |
| 15 | 47.2 | 154.6 | 3.27 | 184.5 | 3.91 |
| 25 | 29.8 | 56.8 | 1.90 | 183.8 | 6.16 |
| 50 | 16.0 | 35.2 | 2.20 | 181.8 | 11.39 |
| 100 | 8.7 | 53.4 | 6.15 | 179.7 | 20.69 |
| 150 | 6.1 | 56.3 | 9.19 | 176.8 | 28.84 |


PyPy 3.11.13 (7.3.20) on 11th Gen Intel(R) Core(TM) i7-1165G7 @ 2.80GHz
----------

GitIgnoreSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 579.4 | - | - | - | - |
| 5 | 123.5 | - | - | - | - |
| 15 | 43.8 | - | - | - | - |
| 25 | 27.2 | - | - | - | - |
| 50 | 11.6 | - | - | - | - |
| 100 | 5.6 | - | - | - | - |
| 150 | 2.9 | - | - | - | - |

PathSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 558.8 | - | - | - | - |
| 5 | 116.0 | - | - | - | - |
| 15 | 45.7 | - | - | - | - |
| 25 | 28.7 | - | - | - | - |
| 50 | 12.7 | - | - | - | - |
| 100 | 6.1 | - | - | - | - |
| 150 | 3.1 | - | - | - | - |


PyPy 3.10.16 (7.3.19) on 11th Gen Intel(R) Core(TM) i7-1165G7 @ 2.80GHz
----------

GitIgnoreSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 589.9 | 106.6 | 0.18 | - | - |
| 5 | 117.2 | 91.9 | 0.78 | - | - |
| 15 | 44.5 | 81.3 | 1.83 | - | - |
| 25 | 27.4 | 44.0 | 1.60 | - | - |
| 50 | 13.0 | 32.1 | 2.48 | - | - |
| 100 | 5.5 | 51.8 | 9.36 | - | - |
| 150 | 3.1 | 47.1 | 15.28 | - | - |

PathSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 581.4 | 106.7 | 0.18 | - | - |
| 5 | 135.7 | 90.7 | 0.67 | - | - |
| 15 | 54.8 | 81.7 | 1.49 | - | - |
| 25 | 31.5 | 43.0 | 1.36 | - | - |
| 50 | 12.5 | 30.2 | 2.41 | - | - |
| 100 | 6.3 | 42.2 | 6.69 | - | - |
| 150 | 3.3 | 44.2 | 13.51 | - | - |


CPython 3.13.11 on AMD RYZEN AI MAX+ 395 w/ Radeon 8060S
----------

GitIgnoreSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 426.1 | 261.3 | 0.61 | 291.5 | 0.68 |
| 5 | 159.6 | 230.2 | 1.44 | 288.5 | 1.81 |
| 15 | 69.4 | 206.5 | 2.97 | 279.3 | 4.02 |
| 25 | 45.8 | 76.5 | 1.67 | 275.9 | 6.02 |
| 50 | 23.6 | 53.9 | 2.29 | 275.1 | 11.66 |
| 100 | 13.4 | 92.4 | 6.91 | 271.3 | 20.29 |
| 150 | 8.7 | 84.6 | 9.70 | 246.5 | 28.26 |

PathSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 439.1 | 282.4 | 0.64 | 289.7 | 0.66 |
| 5 | 163.3 | 244.6 | 1.50 | 291.8 | 1.79 |
| 15 | 76.5 | 214.9 | 2.81 | 272.9 | 3.57 |
| 25 | 48.0 | 78.3 | 1.63 | 271.8 | 5.66 |
| 50 | 23.7 | 50.3 | 2.13 | 268.3 | 11.34 |
| 100 | 13.1 | 77.2 | 5.88 | 264.0 | 20.10 |
| 150 | 9.8 | 79.9 | 8.14 | 263.7 | 26.87 |


PyPy 3.11.13 (7.3.20) on AMD RYZEN AI MAX+ 395 w/ Radeon 8060S
----------

GitIgnoreSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 961.2 | - | - | - | - |
| 5 | 185.0 | - | - | - | - |
| 15 | 69.6 | - | - | - | - |
| 25 | 38.9 | - | - | - | - |
| 50 | 19.1 | - | - | - | - |
| 100 | 10.1 | - | - | - | - |
| 150 | 5.3 | - | - | - | - |

PathSpec.match_files(): 6.5k files

| Patterns | simple<br>ops | hyperscan<br>ops | <br>x | re2<br>ops | <br>x |
| --: | --: | --: | --: | --: | --: |
| 1 | 873.8 | - | - | - | - |
| 5 | 185.6 | - | - | - | - |
| 15 | 70.0 | - | - | - | - |
| 25 | 41.9 | - | - | - | - |
| 50 | 21.5 | - | - | - | - |
| 100 | 10.9 | - | - | - | - |
| 150 | 5.5 | - | - | - | - |
