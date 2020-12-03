#!/bin/bash

set -eu

usage() {
cat << EOF
Pilot integration with Helm.
The plugin allows to prepare local env for running .
Available Commands:
  start    Prepare env for testing
  stop     Remove all the testing resources

Available Flags:
  -n    Namespace to run the test in
EOF
}

run() {
  echo "Successfully pushed!"
}

if [[ $# < 1 ]]; then
  usage
  exit 1
fi

case "${1:-"help"}" in
  "run")
    run
    ;;
  "help")
    usage
    ;;
  "--help")
    usage
    ;;
  "-h")
    usage
    ;;
  *)
    usage
    exit 1
    ;;
esac

exit 0