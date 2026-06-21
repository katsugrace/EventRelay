#!/usr/bin/env bash

HOST=${1:-http://localhost:8000}

SAMPLE_JSON='{
  "object_kind": "pipeline",
  "object_attributes": {"id": 41357, "status": "failed"},
  "commit": {"title": "test(.gitlab-ci): Добавлен тестовый pipeline"}
}'

SAMPLE_JSON_TAGS='{
  "object_kind": "pipeline",
  "object_attributes": {"id": 41357, "status": "failed"},
  "commit": {"title": "test(.gitlab-ci): Добавлен тестовый pipeline"},
  "tags": ["java", "python"]
}'

declare -a CASES=(
  "/test/filters/equals/match:ok"
  "/test/filters/equals/skip:skipped"
  "/test/filters/not_equals/match:ok"
  "/test/filters/not_equals/skip:skipped"
  "/test/filters/in/match:ok"
  "/test/filters/in/skip:skipped"
  "/test/filters/exists/match:ok"
  "/test/filters/exists/skip:skipped"
  "/test/filters/contains/match:ok"
  "/test/filters/contains/skip:skipped"
  "/test/filters/regex/match:ok"
  "/test/filters/regex/skip:skipped"
  "/test/filters/gt/match:ok"
  "/test/filters/gt/skip:skipped"
  "/test/filters/lt/match:ok"
  "/test/filters/lt/skip:skipped"
  "/test/filters/startswith/match:ok"
  "/test/filters/startswith/skip:skipped"
  "/test/filters/endswith/match:ok"
  "/test/filters/endswith/skip:skipped"
)

fail_count=0

for case in "${CASES[@]}"; do
  IFS=":" read -r path expect <<< "$case"
  url="$HOST$path"
  echo -n "POST $url ... "
  PAYLOAD="$SAMPLE_JSON"
  if [[ "$path" == *"/test/filters/in_tags/"* ]]; then
    PAYLOAD="$SAMPLE_JSON_TAGS"
  fi

  resp=$(curl -s -w "\n%{http_code}" -H "Content-Type: application/json" -d "$PAYLOAD" "$url")
  body=$(echo "$resp" | sed '$d')
  code=$(echo "$resp" | tail -n1)

  if [ "$code" != "200" ]; then
    echo "FAIL (http $code)"
    echo "  body: $body"
    fail_count=$((fail_count+1))
    continue
  fi

  if echo "$body" | grep -q '"status"\s*:\s*"ok"'; then
    result=ok
  elif echo "$body" | grep -q '"status"\s*:\s*"skipped"'; then
    result=skipped
  else
    if echo "$body" | grep -q 'error'; then
      echo "FAIL (error response): $body"
      fail_count=$((fail_count+1))
      continue
    fi
    result=unknown
  fi

  if [ "$result" = "$expect" ]; then
    echo "OK ($result)"
  else
    echo "FAIL (expected $expect, got $result)"
    echo "  body: $body"
    fail_count=$((fail_count+1))
  fi

done

if [ $fail_count -eq 0 ]; then
  echo "All checks passed"
  exit 0
else
  echo "$fail_count failures"
  exit 2
fi
