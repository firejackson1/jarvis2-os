package app.jarvis2.remote;

import android.app.Activity;
import android.animation.ValueAnimator;
import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.view.animation.DecelerateInterpolator;
import android.bluetooth.*;
import android.content.*;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.os.Bundle;
import android.media.AudioManager;
import android.media.AudioDeviceInfo;
import android.media.AudioDeviceCallback;
import android.view.*;
import android.widget.*;
import java.util.*;

public class Panel extends Activity {
    private BluetoothAdapter adapter;
    private LinearLayout body;
    private LinearLayout frame;
    private ValueAnimator resize;
    private String page = "bluetooth";
    private String bluetoothFocus = "Pair a new device";
    private TextView state;
    private Button toggle;
    private Button pair;
    private LinearLayout deviceRail;
    private ScrollView railScroll;
    private String selectedDevice;
    private PopupWindow deviceNameBubble;
    private final Map<Integer, BluetoothProfile> profiles = new HashMap<>();
    private boolean closed;
    private BluetoothDevice activeDevice;
    private TextView deviceStatus;
    private LinearLayout discoveryResults;
    private TextView discoveryStatus;
    private AudioSync sync;
    private Runnable syncRefresh;
    private Runnable earRefresh;
    private final Set<String> discovered = new HashSet<>();
    private final BluetoothProfile.ServiceListener listener = new BluetoothProfile.ServiceListener() {
        public void onServiceConnected(int type, BluetoothProfile profile) {
            if (closed) { adapter.closeProfileProxy(type, profile); return; }
            profiles.put(type, profile);
            updateDevices();
        }
        public void onServiceDisconnected(int type) { profiles.remove(type); updateDevices(); }
    };
    private final BroadcastReceiver receiver = new BroadcastReceiver() {
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (BluetoothDevice.ACTION_FOUND.equals(action) && discoveryResults != null) {
                BluetoothDevice device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
                addNearbyDevice(device);
            } else if (BluetoothAdapter.ACTION_DISCOVERY_FINISHED.equals(action) && discoveryStatus != null) {
                discoveryStatus.setText("Nearby devices");
            } else if (BluetoothDevice.ACTION_BOND_STATE_CHANGED.equals(action) && discoveryStatus != null) {
                int bond = intent.getIntExtra(BluetoothDevice.EXTRA_BOND_STATE, BluetoothDevice.BOND_NONE);
                discoveryStatus.setText(bond == BluetoothDevice.BOND_BONDED ? "Paired" :
                        bond == BluetoothDevice.BOND_BONDING ? "Pairing…" : "Pairing ended");
            }
            updateDevices();
            refreshDeviceStatus();
        }
    };

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        sync = AudioSync.get(this);
        adapter = BluetoothAdapter.getDefaultAdapter();
        body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(18), dp(20), dp(18), dp(16));
        GradientDrawable glass = new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{0x99404040, 0xb31b1b1b});
        glass.setCornerRadius(dp(24));
        glass.setStroke(dp(1), 0x60ffffff);
        body.setBackground(glass);
        body.setElevation(dp(16));

        populateBluetooth();
        int contentWidth = dp(220);
        for (int index = 0; index < body.getChildCount(); index++) {
            View child = body.getChildAt(index);
            if (child instanceof TextView) {
                TextView label = (TextView) child;
                int labelWidth = (int) Math.ceil(label.getPaint().measureText(label.getText().toString()))
                        + label.getCompoundPaddingLeft() + label.getCompoundPaddingRight();
                contentWidth = Math.max(contentWidth,
                        labelWidth + body.getPaddingLeft() + body.getPaddingRight() + dp(8));
            }
        }
        frame = new LinearLayout(this);
        frame.setOrientation(LinearLayout.HORIZONTAL);
        frame.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        deviceRail = new LinearLayout(this);
        deviceRail.setOrientation(LinearLayout.VERTICAL);
        railScroll = new ScrollView(this);
        railScroll.setVerticalScrollBarEnabled(false);
        railScroll.setFocusable(false);
        railScroll.setFillViewport(true);
        railScroll.addView(deviceRail);
        LinearLayout.LayoutParams railSize = new LinearLayout.LayoutParams(dp(52), -1);
        railSize.rightMargin = dp(12);
        frame.addView(railScroll, railSize);
        frame.addView(body, new LinearLayout.LayoutParams(contentWidth, -2));
        setContentView(frame);
        Window window = getWindow();
        window.setBackgroundDrawableResource(android.R.color.transparent);
        window.setWindowAnimations(0);
        window.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
        window.setDimAmount(0.28f);
        window.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        WindowManager.LayoutParams attrs = window.getAttributes();
        attrs.width = contentWidth + dp(64);
        attrs.height = WindowManager.LayoutParams.WRAP_CONTENT;
        attrs.x = dp(20);
        window.setAttributes(attrs);
        if (android.os.Build.VERSION.SDK_INT >= 31) window.setBackgroundBlurRadius(dp(36));
        IntentFilter filter = new IntentFilter(BluetoothAdapter.ACTION_STATE_CHANGED);
        filter.addAction(BluetoothDevice.ACTION_ACL_CONNECTED);
        filter.addAction(BluetoothDevice.ACTION_ACL_DISCONNECTED);
        filter.addAction(BluetoothDevice.ACTION_BOND_STATE_CHANGED);
        filter.addAction(BluetoothDevice.ACTION_FOUND);
        filter.addAction(BluetoothAdapter.ACTION_DISCOVERY_FINISHED);
        registerReceiver(receiver, filter);
        updateDevices();
        if (adapter != null) {
            for (int type : new int[]{BluetoothProfile.HEADSET, BluetoothProfile.A2DP, 4})
                adapter.getProfileProxy(this, listener, type);
        }
        ((AudioManager)getSystemService(AUDIO_SERVICE)).registerAudioDeviceCallback(audioCallback, null);
        pair.requestFocus();
        if ("ears".equals(getIntent().getStringExtra("page"))) showEarDetection();
        else if ("sync".equals(getIntent().getStringExtra("page"))) showSync();
        else if ("audio".equals(getIntent().getStringExtra("page"))) showAudio();
        else if ("passthrough".equals(getIntent().getStringExtra("page"))) showPassthrough();
    }

    private void populateBluetooth() {
        TextView title = text("Bluetooth", 22, Color.WHITE);
        body.addView(title);
        state = text("", 15, 0xffdddddd);
        state.setPadding(0, dp(6), 0, dp(14));
        body.addView(state);

        button("Sound output", this::showAudio);
        button("AirPods auto-pause", this::showEarDetection);
        button("Button controls", () -> startActivity(new Intent(this,ControllerSettings.class)));
        pair = button("Pair a new device", this::showDiscovery);
        toggle = button(adapter != null && adapter.isEnabled() ? "Turn Bluetooth off" : "Turn Bluetooth on", () -> {
            if (adapter == null) return;
            if (adapter.isEnabled()) {
                new android.app.AlertDialog.Builder(this).setTitle("Turn Bluetooth off?")
                    .setMessage("The Bluetooth remote will disconnect.")
                    .setNegativeButton("Cancel", null)
                    .setPositiveButton("Turn off", (dialog, which) -> adapter.disable()).show();
            } else adapter.enable();
        });
        button("Close", this::finish);
    }

    private void renderBluetooth() {
        audioView = false;
        soundOutputView = false;
        activeDevice = null;
        deviceStatus = null;
        railScroll.setVisibility(View.VISIBLE);
        body.removeAllViews();
        body.getLayoutParams().width = dp(220);
        body.getLayoutParams().height = ViewGroup.LayoutParams.WRAP_CONTENT;
        WindowManager.LayoutParams bounds = getWindow().getAttributes();
        bounds.width = dp(284);
        bounds.height = WindowManager.LayoutParams.WRAP_CONTENT;
        getWindow().setAttributes(bounds);
        populateBluetooth();
        updateDevices();
        pair.requestFocus();
        for (int i = 0; i < body.getChildCount(); i++) {
            View child = body.getChildAt(i);
            if (child instanceof Button && bluetoothFocus.contentEquals(((Button)child).getText())) child.requestFocus();
        }
    }

    private void navigate(String destination, Runnable render, boolean back) {
        if (closed) return;
        if ("bluetooth".equals(page) && getCurrentFocus() instanceof Button)
            bluetoothFocus = ((Button)getCurrentFocus()).getText().toString();
        if (earRefresh != null) { EarDetection.get(this).unlisten(earRefresh); earRefresh=null; }
        if (resize != null) { resize.cancel(); resize = null; }
        frame.animate().cancel();
        hideDeviceName();
        if (syncRefresh != null) { sync.unlisten(syncRefresh); syncRefresh = null; }
        if (discoveryResults != null) {
            discoveryResults = null;
            discoveryStatus = null;
            stopDiscovery();
        }
        int oldWidth = getWindow().getDecorView().getWidth();
        int oldHeight = getWindow().getDecorView().getHeight();
        page = destination;
        render.run();
        frame.setAlpha(1f);
        frame.setTranslationX(0f);
        if (!frame.isLaidOut() || oldWidth == 0 || !ValueAnimator.areAnimatorsEnabled()) return;
        WindowManager.LayoutParams target = getWindow().getAttributes();
        final int width = target.width;
        final int requestedHeight = target.height;
        if (requestedHeight == WindowManager.LayoutParams.WRAP_CONTENT)
            body.measure(View.MeasureSpec.makeMeasureSpec(body.getLayoutParams().width, View.MeasureSpec.EXACTLY),
                    View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
        final int height = requestedHeight > 0 ? requestedHeight : Math.min(body.getMeasuredHeight(),
                getResources().getDisplayMetrics().heightPixels - dp(40));
        final ValueAnimator animation = ValueAnimator.ofFloat(0f, 1f);
        resize = animation;
        animation.setDuration(180);
        animation.setInterpolator(new DecelerateInterpolator());
        animation.addUpdateListener(value -> {
            float progress = (Float)value.getAnimatedValue();
            WindowManager.LayoutParams bounds = getWindow().getAttributes();
            bounds.width = Math.round(oldWidth + (width - oldWidth) * progress);
            bounds.height = Math.round(oldHeight + (height - oldHeight) * progress);
            getWindow().setAttributes(bounds);
        });
        animation.addListener(new AnimatorListenerAdapter() {
            private boolean cancelled;
            @Override public void onAnimationCancel(Animator animator) { cancelled = true; }
            @Override public void onAnimationEnd(Animator animator) {
                if (cancelled || closed || resize != animation) return;
                WindowManager.LayoutParams bounds = getWindow().getAttributes();
                bounds.width = width;
                bounds.height = requestedHeight;
                getWindow().setAttributes(bounds);
                resize = null;
            }
        });
        frame.setAlpha(0.55f);
        frame.setTranslationX(dp(back ? -10 : 10));
        frame.animate().alpha(1f).translationX(0f).setDuration(180)
                .setInterpolator(new DecelerateInterpolator()).start();
        animation.start();
    }

    private boolean audioView;
    private boolean soundOutputView;
    private final AudioDeviceCallback audioCallback = new AudioDeviceCallback() {
        public void onAudioDevicesAdded(AudioDeviceInfo[] devices) { if (soundOutputView) refreshAudioIcons(); }
        public void onAudioDevicesRemoved(AudioDeviceInfo[] devices) { if (soundOutputView) refreshAudioIcons(); }
    };
    private void showAudio() { navigate("audio", this::renderAudio, false); }

    private void backToAudio() { navigate("audio", this::renderAudio, true); }

    private void renderAudio() {
        if (syncRefresh != null) { sync.unlisten(syncRefresh); syncRefresh = null; }
        audioView = true;
        soundOutputView = true;
        hideDeviceName();
        railScroll.setVisibility(View.VISIBLE);
        body.getLayoutParams().width = dp(220);
        WindowManager.LayoutParams bounds = getWindow().getAttributes();
        bounds.width = body.getLayoutParams().width + dp(64);
        bounds.height = WindowManager.LayoutParams.WRAP_CONTENT;
        getWindow().setAttributes(bounds);
        body.getLayoutParams().height = ViewGroup.LayoutParams.WRAP_CONTENT;
        body.removeAllViews();
        body.addView(text("Sound output", 22, Color.WHITE));
        AudioManager audio = (AudioManager)getSystemService(AUDIO_SERVICE);
        TextView volumeLabel = text("Media volume", 15, 0xffdddddd);
        volumeLabel.setPadding(0, dp(16), 0, dp(4));
        body.addView(volumeLabel);
        SeekBar volume = new SeekBar(this);
        volume.setFocusableInTouchMode(true);
        volume.setContentDescription("Media volume");
        volume.setMax(audio.getStreamMaxVolume(AudioManager.STREAM_MUSIC));
        volume.setProgress(audio.getStreamVolume(AudioManager.STREAM_MUSIC));
        neutralSlider(volume);
        volume.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onStartTrackingTouch(SeekBar bar) {}
            public void onStopTrackingTouch(SeekBar bar) {}
            public void onProgressChanged(SeekBar bar, int value, boolean user) {
                if (user) audio.setStreamVolume(AudioManager.STREAM_MUSIC, value, 0);
            }
        });
        body.addView(volume, new LinearLayout.LayoutParams(-1, dp(42)));
        button("TV + Bluetooth sync", this::showSync);
        button("HDMI passthrough", this::showPassthrough);
        button("Bluetooth", this::backToBluetooth);
        button("Close", this::finish);
        refreshAudioIcons();
        volume.requestFocus();
    }

    private void refreshAudioIcons() {
        if (closed || !soundOutputView) return;
        hideDeviceName();
        deviceRail.removeAllViews();
        AudioManager audio = (AudioManager)getSystemService(AUDIO_SERVICE);
        for (AudioDeviceInfo device : audio.getDevices(AudioManager.GET_DEVICES_OUTPUTS)) {
            int type = device.getType();
            if (type != 2 && type != 3 && type != 4 && type != 8 && type != 9 && type != 11 && type != 22) continue;
            String name = type == 9 ? "TV · HDMI" : type == 2 ? "Built-in speaker" : device.getProductName().toString();
            Button icon = new Button(this);
            icon.setText(type == 9 ? "📺" : type == 2 ? "🔊" : "🎧");
            icon.setTextSize(22);
            icon.setFocusableInTouchMode(true);
            icon.setContentDescription(name);
            icon.setPadding(0, 0, 0, 0);
            icon.setBackground(shape(0x22ffffff, 0x35ffffff));
            icon.setOnFocusChangeListener((view, focused) -> {
                icon.setBackground(shape(focused ? 0xffeeeeee : 0x22ffffff, 0x60ffffff));
                if (focused) showDeviceName(icon, name); else hideDeviceName();
            });
            icon.setOnClickListener(view -> sync.selectOutput(device, () -> {
                if (!closed) Toast.makeText(this, sync.status().startsWith("Could not") ?
                        "Could not select output" : "Playing on " + name, Toast.LENGTH_SHORT).show();
            }));
            LinearLayout.LayoutParams size = new LinearLayout.LayoutParams(dp(46), dp(46));
            size.bottomMargin = dp(8);
            deviceRail.addView(icon, size);
        }
    }

    private void neutralSlider(SeekBar slider) {
        slider.setThumbTintList(android.content.res.ColorStateList.valueOf(Color.WHITE));
        slider.setProgressTintList(android.content.res.ColorStateList.valueOf(0xffdddddd));
        slider.setProgressBackgroundTintList(android.content.res.ColorStateList.valueOf(0xff666666));
    }

    private void neutralSwitch(Switch view) {
        view.setThumbTintList(android.content.res.ColorStateList.valueOf(Color.WHITE));
        view.setTrackTintList(new android.content.res.ColorStateList(
                new int[][]{new int[]{android.R.attr.state_checked}, new int[]{}},
                new int[]{0xff999999, 0xff444444}));
        StateListDrawable background = new StateListDrawable();
        background.addState(new int[]{android.R.attr.state_focused}, shape(0x33ffffff, 0x99ffffff));
        background.addState(new int[]{}, shape(Color.TRANSPARENT, Color.TRANSPARENT));
        view.setBackground(background);
        view.setPadding(dp(6), 0, dp(6), 0);
        view.setFocusableInTouchMode(true);
    }

    private void showSync() { navigate("sync", this::renderSync, false); }

    private void showEarDetection() { navigate("ears", this::renderEarDetection, false); }
    private void renderEarDetection() {
        resetPage("AirPods auto-pause");
        railScroll.setVisibility(View.GONE);
        body.getLayoutParams().width=dp(260);
        body.getLayoutParams().height=ViewGroup.LayoutParams.WRAP_CONTENT;
        WindowManager.LayoutParams bounds=getWindow().getAttributes();
        bounds.width=dp(260);bounds.height=WindowManager.LayoutParams.WRAP_CONTENT;
        getWindow().setAttributes(bounds);
        EarDetection ears=EarDetection.get(this);
        Switch use=new Switch(this);
        use.setText("Pause on removal");use.setTextSize(15);use.setTextColor(Color.WHITE);
        neutralSwitch(use);use.setChecked(ears.enabled());
        body.addView(use,new LinearLayout.LayoutParams(-1,dp(48)));
        Switch resume=new Switch(this);
        resume.setText("Resume on insertion");resume.setTextSize(15);resume.setTextColor(Color.WHITE);
        neutralSwitch(resume);resume.setChecked(ears.autoResume());
        body.addView(resume,new LinearLayout.LayoutParams(-1,dp(48)));
        resume.setOnCheckedChangeListener((view,checked)->ears.setAutoResume(checked));
        TextView status=text(ears.status(),14,Color.WHITE);
        status.setPadding(0,dp(12),0,dp(12));body.addView(status);
        body.addView(text("Removing either AirPod pauses playback. Resume returns only to the same session paused here, within two minutes.",13,0xffdddddd));
        use.setOnCheckedChangeListener((view,checked)->ears.setEnabled(checked));
        earRefresh=()->{if(!closed)status.setText(ears.status());};ears.listen(earRefresh);
        button("Back",this::onBackPressed);use.setFocusableInTouchMode(true);use.requestFocus();
    }

    private void showPassthrough() { navigate("passthrough", this::renderPassthrough, false); }

    private void renderPassthrough() {
        resetPage("HDMI passthrough");
        railScroll.setVisibility(View.GONE);
        body.getLayoutParams().width = dp(260);
        body.getLayoutParams().height = ViewGroup.LayoutParams.MATCH_PARENT;
        WindowManager.LayoutParams bounds = getWindow().getAttributes();
        bounds.width = dp(260);
        bounds.height = Math.min(dp(390), getResources().getDisplayMetrics().heightPixels - dp(40));
        getWindow().setAttributes(bounds);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(content);
        body.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        Switch use = new Switch(this);
        use.setText("Use HDMI bitstream");
        use.setTextSize(15);
        use.setTextColor(Color.WHITE);
        neutralSwitch(use);
        use.setChecked(sync.passthrough());
        content.addView(use, new LinearLayout.LayoutParams(-1, dp(48)));
        TextView support = text(sync.losslessSupport(), 14, Color.WHITE);
        support.setPadding(0, dp(8), 0, dp(10));
        content.addView(support);
        TextView mode = text(sync.losslessStatus(), 13, 0xffdddddd);
        content.addView(mode);
        TextView heading = text("Receiver formats", 15, Color.WHITE);
        heading.setPadding(0, dp(14), 0, dp(6));
        content.addView(heading);
        TextView formats = text(sync.receiverFormats(), 14, 0xffdddddd);
        content.addView(formats);
        TextView help = text("HDMI only. Headphones use decoded audio. Verify lossless playback on your receiver.", 12, 0xffcccccc);
        help.setPadding(0, dp(12), 0, dp(6));
        content.addView(help);
        use.setOnCheckedChangeListener((view, checked) -> {
            if (checked != sync.passthrough()) sync.setPassthrough(checked);
        });
        syncRefresh = () -> {
            if (closed) return;
            use.setEnabled(sync.canBitstream());
            use.setChecked(sync.passthrough());
            support.setText(sync.losslessSupport());
            mode.setText(sync.losslessStatus());
            formats.setText(sync.receiverFormats());
        };
        sync.listen(syncRefresh);
        syncRefresh.run();
        Button back = button("Back", this::backToAudio);
        if (use.isEnabled()) use.requestFocus(); else back.requestFocus();
        sync.refresh();
    }

    private void renderSync() {
        if (syncRefresh != null) sync.unlisten(syncRefresh);
        resetPage("TV + Bluetooth");
        railScroll.setVisibility(View.GONE);
        body.getLayoutParams().width = dp(260);
        body.getLayoutParams().height = ViewGroup.LayoutParams.MATCH_PARENT;
        WindowManager.LayoutParams bounds = getWindow().getAttributes();
        bounds.width = dp(260);
        bounds.height = Math.min(dp(390), getResources().getDisplayMetrics().heightPixels - dp(40));
        getWindow().setAttributes(bounds);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(false);
        scroll.addView(content);
        body.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        TextView device = text(sync.name(), 14, 0xffdddddd);
        device.setMaxLines(2);
        device.setPadding(0, dp(8), 0, dp(6));
        content.addView(device);
        Switch combined = new Switch(this);
        combined.setText("Play on both");
        combined.setTextSize(15);
        combined.setTextColor(Color.WHITE);
        combined.setChecked(sync.enabled());
        neutralSwitch(combined);
        content.addView(combined, new LinearLayout.LayoutParams(-1, dp(44)));
        Switch automatic = new Switch(this);
        automatic.setText("Auto adjustment");
        automatic.setTextSize(15);
        automatic.setTextColor(Color.WHITE);
        automatic.setChecked(sync.automatic());
        neutralSwitch(automatic);
        content.addView(automatic, new LinearLayout.LayoutParams(-1, dp(44)));
        TextView status = text(sync.status(), 14, Color.WHITE);
        status.setPadding(0, dp(6), 0, dp(6));
        content.addView(status);
        TextView delay = text("Saved TV delay · " + sync.calibration() + " ms", 15, Color.WHITE);
        content.addView(delay);
        SeekBar slider = new SeekBar(this);
        slider.setFocusableInTouchMode(true);
        slider.setContentDescription("TV audio delay in milliseconds");
        slider.setMax(400);
        neutralSlider(slider);
        slider.setKeyProgressIncrement(1);
        slider.setProgress(sync.calibration());
        content.addView(slider, new LinearLayout.LayoutParams(-1, dp(40)));
        TextView detail = text(sync.detail(), 12, 0xffcccccc);
        content.addView(detail);
        TextView help = text("Follows reported latency. Fine tuning is saved per device.", 12, 0xffcccccc);
        help.setPadding(0, dp(8), 0, dp(8));
        content.addView(help);
        combined.setOnCheckedChangeListener((view, checked) -> sync.setEnabled(checked));
        automatic.setOnCheckedChangeListener((view, checked) -> sync.setAutomatic(checked));
        slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onStartTrackingTouch(SeekBar bar) {}
            public void onStopTrackingTouch(SeekBar bar) {}
            public void onProgressChanged(SeekBar bar, int value, boolean user) {
                if (user) {
                    delay.setText("Saved TV delay · " + value + " ms");
                    sync.calibrate(value);
                }
            }
        });
        syncRefresh = () -> {
            if (closed) return;
            device.setText(sync.name());
            status.setText(sync.status());
            detail.setText(sync.detail());
            slider.setEnabled(sync.hasDevice());
            slider.setProgress(sync.calibration());
            delay.setText("Saved TV delay · " + sync.calibration() + " ms");
        };
        sync.listen(syncRefresh);
        syncRefresh.run();
        button("Back", this::backToAudio);
        combined.requestFocus();
        sync.refresh();
    }

    private TextView text(String label, int size, int color) {
        TextView text = new TextView(this);
        text.setText(label);
        text.setTextSize(size);
        text.setTextColor(color);
        return text;
    }

    private void updateDevices() {
        if (closed || state == null || audioView) return;
        boolean enabled = adapter != null && adapter.isEnabled();
        state.setText(adapter == null ? "Bluetooth unavailable" : enabled ? "Bluetooth is on" : "Bluetooth is off");
        toggle.setText(enabled ? "Turn Bluetooth off" : "Turn Bluetooth on");
        toggle.setEnabled(adapter != null);
        pair.setEnabled(enabled);
        hideDeviceName();
        deviceRail.removeAllViews();
        if (!enabled) return;
        Set<BluetoothDevice> connected = new HashSet<>();
        for (BluetoothProfile profile : profiles.values()) {
            try { connected.addAll(profile.getConnectedDevices()); } catch (RuntimeException ignored) { }
        }
        List<BluetoothDevice> bonded = new ArrayList<>(adapter.getBondedDevices());
        bonded.sort(Comparator.comparing((BluetoothDevice device) -> !isAudioDevice(device))
                .thenComparing(this::deviceLabel));
        if (selectedDevice == null || bonded.stream().noneMatch(d -> d.getAddress().equals(selectedDevice))) {
            selectedDevice = bonded.isEmpty() ? null : bonded.get(0).getAddress();
        }
        boolean otherGroup = false;
        for (BluetoothDevice device : bonded) {
            if (!isAudioDevice(device) && !otherGroup) {
                deviceRail.addView(new View(this), new LinearLayout.LayoutParams(1, 0, 1));
                otherGroup = true;
            }
            Button icon = new Button(this);
            int major = device.getBluetoothClass() == null ? 0 : device.getBluetoothClass().getMajorDeviceClass();
            icon.setText(major == BluetoothClass.Device.Major.AUDIO_VIDEO ? "🎧" :
                    major == BluetoothClass.Device.Major.PHONE ? "📱" :
                    major == BluetoothClass.Device.Major.PERIPHERAL ? "🎮" : "🔗");
            icon.setTextSize(22);
            icon.setFocusableInTouchMode(true);
            icon.setPadding(0, 0, 0, 0);
            String name = deviceLabel(device);
            icon.setContentDescription(name + (connected.contains(device) ? ", connected" : ", paired"));
            Runnable select = () -> {
                selectedDevice = device.getAddress();
            };
            icon.setOnFocusChangeListener((view, focused) -> {
                icon.setBackground(shape(focused ? 0xffeeeeee : 0x22ffffff, 0x60ffffff));
                if (focused) {
                    select.run();
                    showDeviceName(icon, name);
                } else hideDeviceName();
            });
            icon.setOnClickListener(view -> { select.run(); showDevice(device); });
            icon.setBackground(shape(0x22ffffff, 0x35ffffff));
            LinearLayout.LayoutParams size = new LinearLayout.LayoutParams(dp(46), dp(46));
            size.bottomMargin = dp(8);
            deviceRail.addView(icon, size);
            if (device.getAddress().equals(selectedDevice)) select.run();
        }
        if (!otherGroup) deviceRail.addView(new View(this), new LinearLayout.LayoutParams(1, 0, 1));
    }

    private boolean isAudioDevice(BluetoothDevice device) {
        BluetoothClass deviceClass = device.getBluetoothClass();
        if (deviceClass != null && deviceClass.getMajorDeviceClass() == BluetoothClass.Device.Major.AUDIO_VIDEO) return true;
        android.os.ParcelUuid[] uuids = device.getUuids();
        if (uuids == null) return false;
        for (android.os.ParcelUuid uuid : uuids) {
            String value = uuid.toString();
            if (value.startsWith("0000110b-") || value.startsWith("00001108-")
                    || value.startsWith("0000111e-") || value.startsWith("00001850-")) return true;
        }
        return false;
    }

    private void hideDeviceName() {
        if (deviceNameBubble != null) {
            deviceNameBubble.dismiss();
            deviceNameBubble = null;
        }
    }

    private void showDeviceName(View icon, String name) {
        hideDeviceName();
        TextView label = text(name, 14, Color.WHITE);
        label.setMaxWidth(dp(180));
        label.setPadding(dp(12), dp(8), dp(12), dp(8));
        label.setBackground(shape(0xee252525, 0x66ffffff));
        label.measure(View.MeasureSpec.makeMeasureSpec(dp(180), View.MeasureSpec.AT_MOST),
                View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
        deviceNameBubble = new PopupWindow(label, label.getMeasuredWidth(), label.getMeasuredHeight(), false);
        deviceNameBubble.setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(Color.TRANSPARENT));
        deviceNameBubble.setElevation(dp(6));
        deviceNameBubble.setTouchable(false);
        deviceNameBubble.setIsLaidOutInScreen(true);
        int[] location = new int[2];
        icon.getLocationOnScreen(location);
        deviceNameBubble.showAtLocation(icon, Gravity.TOP | Gravity.LEFT,
                Math.max(dp(8), location[0] - label.getMeasuredWidth() - dp(10)),
                location[1] + (icon.getHeight() - label.getMeasuredHeight()) / 2);
    }

    private String deviceLabel(BluetoothDevice device) {
        try {
            Object alias = BluetoothDevice.class.getMethod("getAlias").invoke(device);
            if (alias instanceof String && !((String) alias).isEmpty()) return (String) alias;
        } catch (Exception ignored) { }
        return device.getName() == null ? device.getAddress() : device.getName();
    }

    private void refreshDeviceStatus() {
        if (closed || activeDevice == null || deviceStatus == null) return;
        String value = activeDevice.getBondState() == BluetoothDevice.BOND_BONDED ? "Paired" : "Not paired";
        try {
            if (Boolean.TRUE.equals(BluetoothDevice.class.getMethod("isConnected").invoke(activeDevice))) value = "Connected";
            int battery = (Integer) BluetoothDevice.class.getMethod("getBatteryLevel").invoke(activeDevice);
            if (battery >= 0 && battery <= 100) value += " · " + battery + "% battery";
        } catch (Exception ignored) { }
        deviceStatus.setText(value);
    }

    @Override public void onBackPressed() {
        if ("main-settings".equals(getIntent().getStringExtra("entry")) && page.equals(getIntent().getStringExtra("page"))) { finish(); return; }
        if ("sync".equals(page) || "passthrough".equals(page)) backToAudio();
        else if (!"bluetooth".equals(page)) backToBluetooth();
        else super.onBackPressed();
    }

    private void resetPage(String title) {
        audioView = true;
        soundOutputView = false;
        activeDevice = null;
        deviceStatus = null;
        hideDeviceName();
        body.removeAllViews();
        body.addView(text(title, 20, Color.WHITE));
    }

    private void backToBluetooth() {
        navigate("bluetooth", this::renderBluetooth, true);
    }

    private void runDeviceAction(BluetoothDevice device, String method, Class<?>[] types, Object... args) {
        try {
            Object result = BluetoothDevice.class.getMethod(method, types).invoke(device, args);
            boolean accepted = !(result instanceof Boolean) || (Boolean)result;
            if (result instanceof Integer) accepted = ((Integer)result) == 0;
            Toast.makeText(this, accepted ? "Request sent" : "Device did not accept the request",
                    Toast.LENGTH_SHORT).show();
        } catch (Exception failure) {
            Toast.makeText(this, "Could not complete this action", Toast.LENGTH_LONG).show();
            android.util.Log.e("JarvisBluetooth", method, failure);
        }
    }

    private final android.bluetooth.le.ScanCallback leCallback = new android.bluetooth.le.ScanCallback() {
        @Override public void onScanResult(int type, android.bluetooth.le.ScanResult result) {
            if (!closed && discoveryResults != null) addNearbyDevice(result.getDevice());
        }
    };

    private void stopDiscovery() {
        if (adapter == null) return;
        adapter.cancelDiscovery();
        android.bluetooth.le.BluetoothLeScanner scanner = adapter.getBluetoothLeScanner();
        if (scanner != null) scanner.stopScan(leCallback);
    }

    private boolean startDiscovery() {
        if (adapter == null || !adapter.isEnabled()) return false;
        boolean classic = adapter.startDiscovery();
        android.bluetooth.le.BluetoothLeScanner scanner = adapter.getBluetoothLeScanner();
        if (scanner != null) scanner.startScan(leCallback);
        return classic || scanner != null;
    }

    private void addNearbyDevice(BluetoothDevice device) {
        if (device != null && discovered.add(device.getAddress())) {
                    Button item = new Button(Panel.this);
                    item.setAllCaps(false);
                    item.setText(device.getName() == null ? device.getAddress() : device.getName());
                    item.setOnClickListener(view -> {
                        stopDiscovery();
                        discoveryStatus.setText("Pairing…");
                if (!device.createBond()) discoveryStatus.setText("Could not start pairing");
                    });
                    discoveryResults.addView(item, new LinearLayout.LayoutParams(-1, dp(46)));
                }
    }

    private void showDiscovery() { navigate("discovery", this::renderDiscovery, false); }

    private void renderDiscovery() {
        resetPage("Pair a device");
        railScroll.setVisibility(View.GONE);
        WindowManager.LayoutParams bounds = getWindow().getAttributes();
        bounds.width = body.getLayoutParams().width;
        bounds.height = Math.min(dp(350), getResources().getDisplayMetrics().heightPixels - dp(40));
        getWindow().setAttributes(bounds);
        body.getLayoutParams().height = ViewGroup.LayoutParams.MATCH_PARENT;
        discoveryStatus = text("Searching…", 14, 0xffdddddd);
        discoveryStatus.setPadding(0, dp(8), 0, dp(12));
        body.addView(discoveryStatus);
        discoveryResults = new LinearLayout(this);
        discoveryResults.setOrientation(LinearLayout.VERTICAL);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(discoveryResults);
        body.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        Button scan = button("Scan again", () -> {
            discovered.clear();
            discoveryResults.removeAllViews();
            stopDiscovery();
            discoveryStatus.setText(startDiscovery() ? "Searching…" : "Could not start scanning");
        });
        button("Back", this::backToBluetooth);
        if (!startDiscovery()) discoveryStatus.setText("Could not start scanning");
        scan.requestFocus();
    }

    private void showDevice(BluetoothDevice device) { navigate("device", () -> renderDevice(device), false); }

    private void renderDevice(BluetoothDevice device) {
        String name = deviceLabel(device);
        resetPage(name);
        activeDevice = device;
        deviceStatus = text("", 14, 0xffdddddd);
        deviceStatus.setPadding(0, dp(8), 0, 0);
        body.addView(deviceStatus);
        refreshDeviceStatus();
        TextView address = text(device.getAddress(), 12, 0xffcccccc);
        address.setPadding(0, dp(8), 0, dp(12));
        body.addView(address);
        Button connect = button("Connect", () -> runDeviceAction(device, "connect", new Class<?>[]{}));
        button("Disconnect", () -> new android.app.AlertDialog.Builder(this)
                .setTitle("Disconnect " + name + "?")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Disconnect", (dialog, which) ->
                        runDeviceAction(device, "disconnect", new Class<?>[]{})).show());
        button("Rename", () -> {
            EditText input = new EditText(this);
            input.setText(name);
            input.setSingleLine(true);
            new android.app.AlertDialog.Builder(this).setTitle("Device name").setView(input)
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Save", (dialog, which) -> {
                    String value = input.getText().toString().trim();
                    if (!value.isEmpty()) runDeviceAction(device, "setAlias", new Class<?>[]{String.class}, value);
                }).show();
        });
        button("Forget device", () -> new android.app.AlertDialog.Builder(this)
                .setTitle("Forget " + name + "?").setMessage("You will need to pair it again.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Forget", (dialog, which) -> {
                    runDeviceAction(device, "removeBond", new Class<?>[]{});
                    backToBluetooth();
                }).show());
        button("Back", this::backToBluetooth);
        connect.requestFocus();
    }

    private Button button(String title, Runnable action) {
        Button button = new Button(this);
        button.setText(title);
        button.setFocusableInTouchMode(true);
        button.setTextSize(15);
        button.setAllCaps(false);
        button.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
        button.setPadding(dp(16), 0, dp(16), 0);
        StateListDrawable background = new StateListDrawable();
        background.addState(new int[]{android.R.attr.state_focused}, shape(0xffeeeeee, 0xffffffff));
        background.addState(new int[]{}, shape(0x22ffffff, 0x35ffffff));
        button.setBackground(background);
        button.setTextColor(new android.content.res.ColorStateList(
                new int[][]{new int[]{android.R.attr.state_focused}, new int[]{}},
                new int[]{0xff151515, Color.WHITE}));
        button.setOnClickListener(view -> action.run());
        LinearLayout.LayoutParams layout = new LinearLayout.LayoutParams(-1, dp(42));
        layout.bottomMargin = dp(10);
        body.addView(button, layout);
        return button;
    }

    private GradientDrawable shape(int fill, int border) {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(fill);
        shape.setCornerRadius(dp(12));
        shape.setStroke(dp(1), border);
        return shape;
    }

    @Override public void onDestroy() {
        closed = true;
        if (earRefresh != null) EarDetection.get(this).unlisten(earRefresh);
        if (resize != null) resize.cancel();
        frame.animate().cancel();
        if (syncRefresh != null) sync.unlisten(syncRefresh);
        if (adapter != null && discoveryResults != null) stopDiscovery();
        hideDeviceName();
        ((AudioManager)getSystemService(AUDIO_SERVICE)).unregisterAudioDeviceCallback(audioCallback);
        unregisterReceiver(receiver);
        if (adapter != null) for (Map.Entry<Integer, BluetoothProfile> entry : new HashMap<>(profiles).entrySet())
            adapter.closeProfileProxy(entry.getKey(), entry.getValue());
        super.onDestroy();
    }
}
