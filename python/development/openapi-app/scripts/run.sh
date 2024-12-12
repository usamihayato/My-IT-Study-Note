# scripts/run.sh
#!/bin/sh
echo "Starting test job..."
echo "Current directory: $(pwd)"
echo "Listing contents of /app/data:"
ls -la /app/data
echo "Listing contents of /app/output:"
ls -la /app/output
echo "Test job completed."