FROM debian:bullseye-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    qemu-system-arm \
    qemu-utils \
    usbutils

WORKDIR /raspi

COPY raspi_sd.img /raspi/raspi_sd.img
COPY kernel8.img /raspi/kernel8.img
COPY bcm2710-rpi-3-b-plus.dtb /raspi/bcm2710-rpi-3-b-plus.dtb

ENV QEMU_AUDIO_DRV=none

CMD ["qemu-system-aarch64", \
    "-M", "raspi3b", \
    "-cpu", "cortex-a53", \
    "-m", "1G", \
    "-kernel", "kernel8.img", \
    "-dtb", "bcm2710-rpi-3-b-plus.dtb", \
    "-drive", "file=raspi_sd.img,format=raw,if=sd", \
    "-nographic", \
    "-serial", "mon:stdio", \
    "-usb", \
    "-device", "usb-host,vendorid=0x1b4f,productid=0x214f"] 