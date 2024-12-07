import subprocess
from pathlib import Path

def get_last_commit_id(file_path):
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", str(file_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )
    return result.stdout.strip()

def get_version_from_commit(commit_id):
    result = subprocess.run(
        ["git", "describe", "--tags", commit_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )
    return result.stdout.strip()

def gen_rst(directory, output_file):
    with open(output_file, 'w') as f:
        f.write("Config History\n")
        f.write("========================\n\n")
        for file_path in Path(directory).rglob('*'):
            if file_path.is_file():
                commit_id = get_last_commit_id(file_path)
                if commit_id:
                    version = get_version_from_commit(commit_id)
                    f.write(f"- **{file_path.name}**: Updated in `{version}`\n")

if __name__ == "__main__":
    dir = "miniscope_io/data/config"
    rst = "docs/history/config.rst"
    gen_rst(dir, rst)