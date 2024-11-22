import os
import subprocess
import shutil

def run_command(command):
    """Runs a shell command and exits on failure."""
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed: {command}")
        exit(1)

def install_dependencies():
    print("Installing dependencies...")
    run_command("sudo apt-get update")
    run_command("sudo apt-get install -y build-essential gfortran wget make openmpi-bin libopenmpi-dev libblas-dev liblapack-dev python3-psutil")

def install_blas_lapack():
    print("Installing BLAS/LAPACK...")
    os.chdir("/tmp")
    if os.path.exists("v3.12.0.tar.gz"):
        os.remove("v3.12.0.tar.gz")
    run_command("wget https://github.com/Reference-LAPACK/lapack/archive/refs/tags/v3.12.0.tar.gz")
    run_command("tar -xzf v3.12.0.tar.gz")
    os.chdir("lapack-3.12.0")
    shutil.copy("make.inc.example", "make.inc")
    run_command("make blaslib -j$(nproc)")
    run_command("make lapacklib -j$(nproc)")

def install_hpl():
    print("Installing HPL...")
    os.chdir("/tmp")
    if os.path.exists("hpl-2.3.tar.gz"):
        os.remove("hpl-2.3.tar.gz")
    run_command("wget https://www.netlib.org/benchmark/hpl/hpl-2.3.tar.gz")
    run_command("tar -xzf hpl-2.3.tar.gz")
    os.chdir("hpl-2.3")
    run_command("./configure LDFLAGS='-L../lapack-3.12.0' LIBS='-llapack -lblas' CC=mpicc --prefix=/usr/local/hpl")
    run_command("make -j$(nproc)")
    run_command("sudo make install")

def cleanup():
    print("Cleaning up...")
    run_command("rm -rf /tmp/lapack-3.12.0*")
    run_command("rm -rf /tmp/hpl-2.3*")

def main():
    install_dependencies()
    install_blas_lapack()
    install_hpl()
    cleanup()
    print("Installation completed!")
    print("HPL binary location: /usr/local/hpl/bin/xhpl")

if __name__ == "__main__":
    main()
