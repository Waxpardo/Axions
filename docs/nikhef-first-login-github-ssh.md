# First Nikhef Login and GitHub SSH Setup

This guide walks through the first-time workflow for:

- Logging in to Nikhef.
- Entering a Stoomboot interactive node.
- Creating your personal directory under `/data/alice`.
- Creating a GitHub SSH key on Nikhef.
- Adding that key to GitHub.
- Cloning the Axions repository.

Replace these placeholders before running commands:

```text
username                      your Nikhef username
your_github_email@example.com your GitHub account email address
```

## 1. Log In To Nikhef

From your laptop terminal:

```bash
ssh -X -Y username@login.nikhef.nl
```

Then from the Nikhef login node, connect to a Stoomboot interactive node:

```bash
ssh -X -Y username@stbc-i1
```

If `stbc-i1` is busy or unavailable, use another interactive Stoomboot node
recommended by Nikhef, for example `stbc-i2` or `stbc-i3`.

## 2. Create Your Personal Directory Under `/data/alice`

Once you are on the Stoomboot node:

```bash
cd /data/alice/
mkdir username
cd username/
```

Check that you are in the right place:

```bash
pwd
```

You should see:

```text
/data/alice/username
```

## 3. Create A GitHub SSH Key On Nikhef

Run this on Nikhef, not on your laptop:

```bash
ssh-keygen -t ed25519 -C "your_github_email@example.com" -f ~/.ssh/id_ed25519_github
```

When it asks for a passphrase, use one if possible. This creates:

```text
~/.ssh/id_ed25519_github      private key, never share this
~/.ssh/id_ed25519_github.pub  public key, this goes into GitHub
```

Fix the permissions:

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519_github
chmod 644 ~/.ssh/id_ed25519_github.pub
```

## 4. Tell SSH To Use This Key For GitHub

Open your SSH config on Nikhef:

```bash
nano ~/.ssh/config
```

Add this block:

```sshconfig
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes
```

Save and exit:

```text
Ctrl+O, Enter, Ctrl+X
```

Fix the config permissions:

```bash
chmod 600 ~/.ssh/config
```

## 5. Copy Your Public Key

Print the public key:

```bash
cat ~/.ssh/id_ed25519_github.pub
```

Copy the entire output line. It should start with:

```text
ssh-ed25519
```

Do not copy or share the private key:

```text
~/.ssh/id_ed25519_github
```

## 6. Add The Key To GitHub

In your browser:

1. Go to GitHub.
2. Click your profile picture in the top-right corner.
3. Open `Settings`.
4. Open `SSH and GPG keys`.
5. Click `New SSH key`.
6. Give it a title such as `Nikhef Stoomboot`.
7. Choose `Authentication Key`.
8. Paste the public key from `id_ed25519_github.pub`.
9. Click `Add SSH key`.

## 7. Test The GitHub Connection

Back on Nikhef:

```bash
ssh -T git@github.com
```

The first time, SSH may ask whether you trust GitHub's host key. Type:

```text
yes
```

A successful connection looks like:

```text
Hi github-username! You've successfully authenticated, but GitHub does not provide shell access.
```

That message is good. It means GitHub recognizes your Nikhef SSH key.

## 8. Clone The Axions Repository

Go to your personal Alice directory:

```bash
cd /data/alice/username/
```

Clone the repository using the SSH URL:

```bash
git clone git@github.com:Waxpardo/Axions.git
```

Enter the repository:

```bash
cd Axions
```

Check the remote:

```bash
git remote -v
```

You should see:

```text
origin  git@github.com:Waxpardo/Axions.git (fetch)
origin  git@github.com:Waxpardo/Axions.git (push)
```

## 9. Set Your Git Identity On Nikhef

Do this once on Nikhef:

```bash
git config --global user.name "Your Name"
git config --global user.email "your_github_email@example.com"
```

Check:

```bash
git config --global --list
```

## 10. Normal Git Workflow

Inside the repository:

```bash
git status
git pull
git add .
git commit -m "Describe your change"
git push origin main
```

## Troubleshooting

If `git push` asks for:

```text
Username for 'https://github.com':
```

then the repository is using HTTPS instead of SSH. Fix it inside the repository:

```bash
git remote set-url origin git@github.com:Waxpardo/Axions.git
git remote set-url --push origin git@github.com:Waxpardo/Axions.git
```

If `ssh -T git@github.com` says `Permission denied (publickey)`, check:

```bash
ls -la ~/.ssh
cat ~/.ssh/config
cat ~/.ssh/id_ed25519_github.pub
```

Make sure the public key shown by `cat ~/.ssh/id_ed25519_github.pub` is the same
one added to GitHub.

If Git prints warnings about `libz.so.1` while an ALICE/ROOT environment is
loaded, leave that environment before doing Git work or run:

```bash
env -u LD_LIBRARY_PATH git status
```

