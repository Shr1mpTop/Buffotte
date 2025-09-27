import argparse
import subprocess
import sys
import os

ROOT = os.path.dirname(__file__)


def run_script(script, args=None):
    cmd = [sys.executable, os.path.join(ROOT, script)]
    if args:
        cmd += args
    print('Running:', ' '.join(cmd))
    res = subprocess.run(cmd)
    return res.returncode


def main():
    parser = argparse.ArgumentParser(prog='buffotte', description='Buffotte CLI')
    sub = parser.add_subparsers(dest='cmd')

    p_fetch = sub.add_parser('fetch', help='Fetch latest kline and insert into DB')
    p_fetch.add_argument('--config', '-c', default='config.json')

    p_predict = sub.add_parser('predict', help='Run next-week prediction')
    p_predict.add_argument('--output', '-o', default='models/next_week_prediction.json')

    p_report = sub.add_parser('report', help='Run full daily report (fetch+predict+email)')

    p_analysis = sub.add_parser('analyze', help='Run analysis postprocess')

    args, extra = parser.parse_known_args()
    if args.cmd == 'fetch':
        return run_script('kline_crawler.py', ['--mode', 'recent', '--type', 'day', '--config', args.config])
    if args.cmd == 'predict':
        return run_script('predict_next_week.py')
    if args.cmd == 'report':
        return run_script('run_daily_report.py')
    if args.cmd == 'analyze':
        return run_script('analysis_postprocess.py')
    parser.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
