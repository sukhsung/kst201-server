#!/bin/bash
set -e

SERVICE_NAME="kst201-server"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PYTHON=$HOME/venv-kst/bin/python3
WORKDIR=$(pwd)
RUN_USER=$USER

echo "Installing ${SERVICE_NAME} as a systemd service..."
echo "  User:             ${RUN_USER}"
echo "  WorkingDirectory: ${WORKDIR}"
echo "  Python:           ${PYTHON}"

sudo tee "${SERVICE_FILE}" > /dev/null <<EOF
[Unit]
Description=KST201 Server
After=network.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${WORKDIR}
ExecStart=${PYTHON} kst201-server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

echo "Done. Service status:"
sudo systemctl status "${SERVICE_NAME}" --no-pager
