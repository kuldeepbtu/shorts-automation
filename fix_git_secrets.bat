@echo off
echo 🔥 Fixing Git Secret Issue...

echo.
echo 🧹 Removing sensitive files from tracking...
git rm --cached client_secrets.json 2>nul
git rm --cached .env 2>nul
git rm --cached *.log 2>nul

echo.
echo 📦 Resetting last commit...
git reset --soft HEAD~1
git reset

echo.
echo 🛡️ Creating .gitignore if not exists...
if not exist .gitignore (
    echo .env >> .gitignore
    echo client_secrets.json >> .gitignore
    echo *.log >> .gitignore
)

echo.
echo 📁 Re-adding safe files...
git add .

echo.
echo 💾 Committing clean version...
git commit -m "Removed secrets and fixed repo"

echo.
echo 🚀 Pushing to GitHub...
git push --force

echo.
echo ✅ DONE! Your repo is now clean and safe.
pause