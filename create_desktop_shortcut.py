import os
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def create_shortcut():
    """Tự động tạo Shortcut 'Trợ Lý Yêu Thương' ra Desktop và thư mục Startup với icon trái tim."""
    base_dir = Path(__file__).resolve().parent
    bat_file = base_dir / "TroLyYeuThuong.bat"
    icon_file = base_dir / "heart.ico"
    
    ps_script = f"""
    $desktop = [Environment]::GetFolderPath('Desktop');
    $startup = [Environment]::GetFolderPath('Startup');
    $WshShell = New-Object -ComObject WScript.Shell;
    
    # Tao shortcut tren Desktop
    if (Test-Path $desktop) {{
        $scDesktop = $WshShell.CreateShortcut((Join-Path $desktop "Tro Ly Yeu Thuong.lnk"));
        $scDesktop.TargetPath = "{bat_file}";
        $scDesktop.WorkingDirectory = "{base_dir}";
        $scDesktop.IconLocation = "{icon_file}";
        $scDesktop.Description = "Tro Ly Yeu Thuong - Danh tang Em Be";
        $scDesktop.Save();
        Write-Output "Da tao Shortcut tren Desktop!";
    }}
    
    # Tao shortcut tai Startup
    if (Test-Path $startup) {{
        $scStartup = $WshShell.CreateShortcut((Join-Path $startup "TroLyYeuThuong.lnk"));
        $scStartup.TargetPath = "{bat_file}";
        $scStartup.WorkingDirectory = "{base_dir}";
        $scStartup.IconLocation = "{icon_file}";
        $scStartup.Description = "Tro Ly Yeu Thuong";
        $scStartup.Save();
        Write-Output "Da thiet lap tu khoi dong Windows Startup!";
    }}
    """
    import subprocess
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("Lỗi:", res.stderr)


if __name__ == "__main__":
    create_shortcut()
