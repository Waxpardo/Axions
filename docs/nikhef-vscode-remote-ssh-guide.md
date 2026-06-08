# VS Code Remote-SSH Setup for Nikhef/Stoomboot

This guide sets up a one-click-ish VS Code connection from a local laptop to a
Nikhef Stoomboot interactive node, opening the project directory on the remote
filesystem.

Sources:

- Nikhef Stoomboot documentation: https://kb.nikhef.nl/ct/Stoomboot_cluster.html
- Nikhef SSH/ProxyJump documentation: https://kb.nikhef.nl/ct/SSH_access_and_configuration.html
- VS Code Remote-SSH documentation: https://code.visualstudio.com/docs/remote/ssh
- VS Code Remote-SSH troubleshooting: https://code.visualstudio.com/docs/remote/troubleshooting

## What This Does

The setup has three pieces:

1. A local SSH key that lets your laptop log in to Nikhef.
2. A local SSH config with a jump through `login.nikhef.nl` to a Stoomboot node.
3. A VS Code `.code-workspace` file that opens the remote folder directly.

The old local setup used these names:

```sshconfig
Host nikhef
Host stbc
Host stbc-vscodium
```

The important detail is that the VS Code host alias should not use
`RemoteCommand` or force a TTY. VS Code Remote-SSH needs a clean SSH session so
it can start its remote server.

## Placeholders

Replace these values everywhere in the commands below:

```text
NIKHEF_USER    your Nikhef username
REMOTE_DIR     your working directory, for example /data/alice/NIKHEF_USER
STBC_NODE      an interactive Stoomboot node, for example stbc-i3.nikhef.nl
```

Use an interactive node such as `stbc-i1.nikhef.nl`, `stbc-i2.nikhef.nl`, or
`stbc-i3.nikhef.nl`, depending on what Nikhef currently recommends and what is
available.

## macOS Setup

### 1. Install VS Code and Remote-SSH

Install Visual Studio Code:

```text
https://code.visualstudio.com/
```

In VS Code, install the extension:

```text
Remote - SSH
```

Optional but useful: install the `code` command in your shell:

```text
Cmd+Shift+P -> Shell Command: Install 'code' command in PATH
```

### 2. Create a Local SSH Key

On your Mac:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_nikhef -C "nikhef-vscode"
```

Use a passphrase if possible.

### 3. Copy the Public Key to Nikhef

If `ssh-copy-id` is available:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_nikhef.pub NIKHEF_USER@login.nikhef.nl
```

If `ssh-copy-id` is not available:

```bash
cat ~/.ssh/id_ed25519_nikhef.pub | ssh NIKHEF_USER@login.nikhef.nl 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
```

Test the login:

```bash
ssh -i ~/.ssh/id_ed25519_nikhef NIKHEF_USER@login.nikhef.nl
```

Exit back to your Mac:

```bash
exit
```

### 4. Create the Local SSH Config

Edit:

```bash
nano ~/.ssh/config
```

Add:

```sshconfig
Host *
    ServerAliveInterval 30
    ServerAliveCountMax 3

Host nikhef
    HostName login.nikhef.nl
    User NIKHEF_USER
    ForwardAgent yes
    IdentityFile ~/.ssh/id_ed25519_nikhef

Host stbc
    HostName STBC_NODE
    User NIKHEF_USER
    ProxyJump nikhef
    IdentityFile ~/.ssh/id_ed25519_nikhef

Host stbc-vscode
    HostName STBC_NODE
    User NIKHEF_USER
    ProxyJump nikhef
    IdentityFile ~/.ssh/id_ed25519_nikhef
    RequestTTY no
```

Fix permissions:

```bash
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/id_ed25519_nikhef
chmod 644 ~/.ssh/id_ed25519_nikhef.pub
```

Test:

```bash
ssh nikhef
exit
ssh stbc-vscode
exit
```

### 5. Create the VS Code Workspace File

Create `~/Desktop/Nikhef.code-workspace`:

```bash
nano ~/Desktop/Nikhef.code-workspace
```

Put this inside:

```json
{
  "folders": [
    {
      "uri": "vscode-remote://ssh-remote+stbc-vscode/REMOTE_DIR"
    }
  ],
  "remoteAuthority": "ssh-remote+stbc-vscode",
  "settings": {}
}
```

Example:

```json
{
  "folders": [
    {
      "uri": "vscode-remote://ssh-remote+stbc-vscode/data/alice/NIKHEF_USER"
    }
  ],
  "remoteAuthority": "ssh-remote+stbc-vscode",
  "settings": {}
}
```

Open it:

```bash
code --reuse-window ~/Desktop/Nikhef.code-workspace
```

Or double-click the workspace file from Finder.

### 6. Optional macOS Launcher

Create `~/Desktop/Nikhef`:

```bash
nano ~/Desktop/Nikhef
```

Use this for Microsoft VS Code:

```bash
#!/usr/bin/env bash
set -euo pipefail
exec code --reuse-window "${HOME}/Desktop/Nikhef.code-workspace"
```

Use this for VSCodium:

```bash
#!/usr/bin/env bash
set -euo pipefail
exec codium --reuse-window "${HOME}/Desktop/Nikhef.code-workspace"
```

Make it executable:

```bash
chmod +x ~/Desktop/Nikhef
```

Then run:

```bash
~/Desktop/Nikhef
```

## Windows Setup

These instructions use Windows PowerShell and the built-in Windows OpenSSH
client. Use the normal Windows VS Code, not the WSL VS Code, unless you
deliberately want to maintain a separate WSL SSH setup.

### 1. Install VS Code and Remote-SSH

Install Visual Studio Code:

```text
https://code.visualstudio.com/
```

During install, enable:

```text
Add to PATH
```

In VS Code, install:

```text
Remote - SSH
```

Check that Windows can run SSH:

```powershell
ssh -V
```

### 2. Create a Local SSH Key

In PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\.ssh"
ssh-keygen -t ed25519 -f "$HOME\.ssh\id_ed25519_nikhef" -C "nikhef-vscode"
```

Use a passphrase if possible.

### 3. Copy the Public Key to Nikhef

In PowerShell:

```powershell
type "$HOME\.ssh\id_ed25519_nikhef.pub" | ssh NIKHEF_USER@login.nikhef.nl "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

Test:

```powershell
ssh -i "$HOME\.ssh\id_ed25519_nikhef" NIKHEF_USER@login.nikhef.nl
```

Exit back to Windows:

```bash
exit
```

### 4. Create the Windows SSH Config

Create or edit:

```powershell
notepad "$HOME\.ssh\config"
```

Put this inside:

```sshconfig
Host *
    ServerAliveInterval 30
    ServerAliveCountMax 3

Host nikhef
    HostName login.nikhef.nl
    User NIKHEF_USER
    ForwardAgent yes
    IdentityFile ~/.ssh/id_ed25519_nikhef

Host stbc
    HostName STBC_NODE
    User NIKHEF_USER
    ProxyJump nikhef
    IdentityFile ~/.ssh/id_ed25519_nikhef

Host stbc-vscode
    HostName STBC_NODE
    User NIKHEF_USER
    ProxyJump nikhef
    IdentityFile ~/.ssh/id_ed25519_nikhef
    RequestTTY no
```

Test:

```powershell
ssh nikhef
exit
ssh stbc-vscode
exit
```

If VS Code cannot find SSH, set the VS Code setting `remote.SSH.path` to:

```text
C:\Windows\System32\OpenSSH\ssh.exe
```

### 5. Create the VS Code Workspace File

Create:

```powershell
notepad "$HOME\Desktop\Nikhef.code-workspace"
```

Put this inside:

```json
{
  "folders": [
    {
      "uri": "vscode-remote://ssh-remote+stbc-vscode/REMOTE_DIR"
    }
  ],
  "remoteAuthority": "ssh-remote+stbc-vscode",
  "settings": {}
}
```

Example:

```json
{
  "folders": [
    {
      "uri": "vscode-remote://ssh-remote+stbc-vscode/data/alice/NIKHEF_USER"
    }
  ],
  "remoteAuthority": "ssh-remote+stbc-vscode",
  "settings": {}
}
```

Open it:

```powershell
code "$HOME\Desktop\Nikhef.code-workspace"
```

Or double-click the `.code-workspace` file from the Desktop.

### 6. Optional Windows Launcher

Create:

```powershell
notepad "$HOME\Desktop\Nikhef-VSCode.bat"
```

Put this inside:

```bat
@echo off
code "%USERPROFILE%\Desktop\Nikhef.code-workspace"
```

If `code` is not on PATH, use the direct executable path instead:

```bat
@echo off
"%LocalAppData%\Programs\Microsoft VS Code\Code.exe" "%USERPROFILE%\Desktop\Nikhef.code-workspace"
```

Double-click `Nikhef-VSCode.bat` to open the remote workspace.

## Using VS Code After Setup

Open the workspace file. The first connection can take a while because VS Code
installs its remote server under your home directory on Nikhef, usually in:

```text
~/.vscode-server
```

Once connected, open a terminal in VS Code:

```text
Terminal -> New Terminal
```

That terminal runs on the Stoomboot node, not on your laptop.

Then go to your project:

```bash
cd REMOTE_DIR
```

For example:

```bash
cd /data/alice/NIKHEF_USER/Axions
```

## Cloning a GitHub Repository on Nikhef

Inside the VS Code remote terminal:

```bash
cd /data/alice/NIKHEF_USER
git clone git@github.com:OWNER/REPOSITORY.git
```

For this project:

```bash
git clone git@github.com:Waxpardo/Axions.git
```

If GitHub asks for a username and password, the remote is using HTTPS instead of
SSH. Switch it:

```bash
git remote set-url origin git@github.com:Waxpardo/Axions.git
git remote set-url --push origin git@github.com:Waxpardo/Axions.git
```

## Common Problems

### VS Code keeps asking for passwords

Check the plain SSH command first:

```bash
ssh stbc-vscode
```

If plain SSH asks for a password, VS Code will too. Check that the local public
key is in `~/.ssh/authorized_keys` on Nikhef and that permissions are correct:

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### Direct Stoomboot SSH fails from home

That is expected from many networks. Use the `ProxyJump nikhef` config shown
above, or use eduVPN with institute access.

### VS Code fails but normal SSH works

Use the `stbc-vscode` host, not a host that has `RemoteCommand` or
`RequestTTY yes`. Remote commands and forced TTY sessions can interfere with the
VS Code server startup.

### Windows VS Code does not see WSL SSH config

Windows VS Code reads the Windows SSH config:

```text
C:\Users\YOUR_WINDOWS_USER\.ssh\config
```

It does not automatically read:

```text
~/.ssh/config
```

inside WSL. Keep the config in Windows unless you intentionally configure VS
Code to use WSL's SSH executable.

### ROOT or ALICE environment breaks VS Code/Git

Avoid auto-loading ROOT, AliEn, or `alienv enter ...` from `.bashrc` or
`.bash_profile` for the account VS Code logs into. Load those environments
manually only inside project terminals:

```bash
source /cvmfs/alice.cern.ch/etc/login.sh
alienv enter VO_ALICE@ROOT::v6-30-01-alice5-2
```

If Git prints warnings about an old `libz.so.1`, leave the ALICE/ROOT
environment before doing Git work:

```bash
module purge
```

or run Git without the polluted library path:

```bash
env -u LD_LIBRARY_PATH git status
```

## Security Notes

Do not put passwords in notes, workspace files, Git repositories, or SSH config
files. SSH config files should contain usernames, hostnames, and key paths only.

Do not share private keys:

```text
id_ed25519_nikhef
```

Sharing the public key is fine:

```text
id_ed25519_nikhef.pub
```
