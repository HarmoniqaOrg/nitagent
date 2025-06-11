import logging

from .scraper import process_csv

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AISBL scraping agent")
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    process_csv(args.input_csv, args.output_csv)
