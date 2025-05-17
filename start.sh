#!/bin/bash

# QEMU 실행
exec qemu-system-aarch64 \
    -M raspi3b \
    -cpu cortex-a53 \
    -m 1G \
    -smp 4 \
    -kernel kernel8.img \
    -dtb bcm2710-rpi-3-b-plus.dtb \
    -drive file=raspi_sd.img,format=raw,if=sd \
    -nographic \
    -serial mon:stdio \
    -append "console=ttyAMA0 root=/dev/mmcblk0p2 rw rootwait" \
    -usb \
    -device pci-bridge,chassis_nr=1 \
    -device usb-ehci,bus=pci.1 \
    -device usb-host,hostbus=1,hostaddr=1 \
    -no-reboot 