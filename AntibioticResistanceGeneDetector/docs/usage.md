# Usage

## Basic CLI Example
```sh
arg_res_detector --input input/example.fasta --db data/resistance_genes.fasta --map data/gene_class_map.csv
```

## Batch Processing
```sh
arg_res_detector --input input/ --db data/resistance_genes.fasta --map data/gene_class_map.csv --outdir output/
```

## Rich Output
Rich tables and progress bars are enabled by default. Use `--no-rich` to disable.
