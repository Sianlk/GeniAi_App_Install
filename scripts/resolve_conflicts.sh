#!/bin/bash
echo "🔧 Starting conflict resolver"
git fetch --all
git checkout main
git merge --strategy-option theirs origin/geniqx || git merge --strategy-option ours origin/geniqx
git add .
git commit -m "Resolved conflicts between main and geniqx"
git push origin main
echo "✅ Conflicts resolved and merged!"
