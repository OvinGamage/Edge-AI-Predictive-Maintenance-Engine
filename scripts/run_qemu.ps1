param(
    [string]$FirmwarePath = "build/clang-cmake/firmware/firmware_app.elf",
    [int]$Port = 5555
)

$docker = Get-Command docker.exe -ErrorAction SilentlyContinue
if (-not $docker) {
    throw "Docker CLI was not found on PATH. Start Docker Desktop and verify 'docker info'."
}

if (-not (Test-Path $FirmwarePath)) {
    throw "Firmware ELF not found: $FirmwarePath. Build the ARM target first."
}

$chardev = "socket,id=uart0,host=0.0.0.0,port=5555,server=on,wait=on"
& $docker.Source compose run --rm -p "127.0.0.1:${Port}:5555" dev-environment `
    qemu-system-arm -M mps2-an385 -cpu cortex-m3 -kernel $FirmwarePath `
    -display none -monitor none -chardev $chardev -serial chardev:uart0
