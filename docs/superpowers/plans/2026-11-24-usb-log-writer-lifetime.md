# USB log writer connection lifetime

> Execute inline with superpowers:executing-plans under standing owner
> delegation. Build/test offline; do not reboot for this source task.

**Goal:** Keep the gadget TTY open between configuration and periodic snapshots,
so setup does not itself signal a disconnected terminal before data is read.

**Design:** The owned background writer opens a single read/write descriptor,
configures that descriptor through stty's standard input and writes each finite
log snapshot through it. On failure it closes/retries after a delay. Its normal
stdin remains the private null node; no application reads USB input. Preserve
periodic writes so idle host disconnect/reconnect can be noticed without new
log data. Keep all gadget, identity and storage exclusion checks unchanged.

**Evidence:** The exact matching GKI common revision's gs_close calls the ACM
disconnect callback on the last TTY close; acm_disconnect clears DCD/DSR. The
current writer closes after stty and every cat. This is a source-backed candidate
mechanism for the zero-byte hardware result, not a confirmed hardware cause.

**Task / checks:**

- [x] Add a failing safe fixture that models carrier loss when stty closes with
  no parent-held terminal descriptor; preserve host-absence and idle retry tests.
- [x] Keep one descriptor open while configuring and sending snapshots; retry
  a failed connection and keep the parent asynchronous.
- [x] Run all host checks and actual ARM64 BusyBox guard tests with privileged
  commands substituted; use a private PTY to verify real stty descriptor setup.
- [ ] Obtain a fresh read-only review, document actual evidence and limitations,
  commit/publish source and build deterministic private artifacts if qualified.

**Source reference:** kernel/common 3d26c188ef7e87e52ea1fa0092db760a55e2ae4c,
drivers/usb/gadget/function/{u_serial.c,f_acm.c}. The public GKI/kernel payload
correspondence is recorded in the OS repository, KERNEL_SOURCE_PROVENANCE.md.
