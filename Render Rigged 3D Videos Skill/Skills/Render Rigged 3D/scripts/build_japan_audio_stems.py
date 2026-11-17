import os
import wave
import subprocess
import numpy as np
from scipy import signal

SCRATCH_DIR = r"C:\Users\WayWe Work-Station\.gemini\antigravity\brain\8ad88795-d9fa-438b-8430-13b89b7ef998\scratch\japan_job_project"
OUT_DIR = r"C:\Users\WayWe Work-Station\Downloads\Mate\Job Culture of japan"
VO_WAV = os.path.join(SCRATCH_DIR, "user_vo.wav")

SR = 44100


def read_vo(path):
    with wave.open(path, "rb") as wf:
        n = wf.getnframes()
        raw = wf.readframes(n)
        audio = np.frombuffer(raw, dtype=np.int16).reshape(-1, 2).astype(np.float32) / 32768.0
    return audio


def write_wav_and_mp3(base_path_no_ext, stereo_float):
    clipped = np.clip(stereo_float, -0.99, 0.99)
    pcm = (clipped * 32767.0).astype(np.int16)
    wav_path = base_path_no_ext + ".wav"
    mp3_path = base_path_no_ext + ".mp3"
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", wav_path, "-c:a", "libmp3lame", "-b:a", "192k", mp3_path],
        check=True,
    )


def add_stereo(buf, start_s, sig_l, sig_r=None, gain=1.0):
    if sig_r is None:
        sig_r = sig_l
    i0 = max(0, int(start_s * SR))
    n = min(len(sig_l), len(buf) - i0)
    if n <= 0:
        return
    buf[i0 : i0 + n, 0] += sig_l[:n] * gain
    buf[i0 : i0 + n, 1] += sig_r[:n] * gain


def bandpass(sig, f_lo, f_hi, order=4):
    nyq = 0.5 * SR
    b, a = signal.butter(order, [max(20.0, f_lo) / nyq, min(nyq - 100.0, f_hi) / nyq], btype="band")
    return signal.lfilter(b, a, sig)


def sfx_jammed_fire_button():
    """
    Repeated plastic-and-spring red button mashing ('FIRE EMPLOYEE') + rocket seat sputter.
    """
    dur = 2.35
    n = int(dur * SR)
    out = np.zeros(n)
    rng = np.random.default_rng(101)

    for bt in [0.08, 0.28, 0.48, 0.72, 1.82, 2.02]:
        i0 = int(bt * SR)
        cn = int(0.09 * SR)
        st = np.linspace(0, 0.09, cn, endpoint=False)
        click = (
            0.65 * np.sin(2 * np.pi * (480 * np.exp(-st * 28)) * st) * np.exp(-st * 35)
            + 0.45 * np.sin(2 * np.pi * 1620 * st) * np.exp(-st * 85)
            + 0.40 * bandpass(rng.standard_normal(cn), 800, 4200) * np.exp(-st * 90)
        ) * 0.75
        out[i0 : min(n, i0 + cn)] += click[: min(n, i0 + cn) - i0]

    # Ejector seat air hiss / sputter at t=1.10..1.65s
    i_ej = int(1.10 * SR)
    n_ej = int(0.55 * SR)
    st = np.linspace(0, 0.55, n_ej, endpoint=False)
    sputter = bandpass(rng.standard_normal(n_ej), 500, 4800) * np.sin(np.pi * st / 0.55) * (0.5 + 0.5 * np.sin(2 * np.pi * 18 * st)) * 0.55
    out[i_ej : i_ej + n_ej] += sputter
    return out * 0.95, out * 1.05


def sfx_storage_key_jingle(dur_s=1.8):
    n = int(dur_s * SR)
    out = np.zeros(n)
    rng = np.random.default_rng(202)
    for k, kt in enumerate([0.10, 0.24, 0.42, 0.65, 0.88, 1.15, 1.38]):
        i0 = int(kt * SR)
        kn = int(0.14 * SR)
        st = np.linspace(0, 0.14, kn, endpoint=False)
        f1 = 3100 + (k % 3) * 420
        f2 = f1 * 1.44
        clink = (
            0.55 * np.sin(2 * np.pi * f1 * st)
            + 0.40 * np.sin(2 * np.pi * f2 * st)
            + 0.25 * np.sin(2 * np.pi * 6200 * st)
        ) * np.exp(-st * 42) * 0.48
        out[i0 : min(n, i0 + kn)] += clink[: min(n, i0 + kn) - i0]
    return out * 0.92, out * 1.08


def sfx_office_walk_and_door_open(dur_s=3.4):
    n = int(dur_s * SR)
    t = np.linspace(0, dur_s, n, endpoint=False)
    rng = np.random.default_rng(303)
    out = np.zeros(n)

    # Footsteps (0.1..2.1s)
    for st_t in np.arange(0.12, 2.10, 0.36):
        i0 = int(st_t * SR)
        sn = int(0.08 * SR)
        st = np.linspace(0, 0.08, sn, endpoint=False)
        step = (
            0.55 * np.sin(2 * np.pi * (145 * np.exp(-st * 30)) * st) * np.exp(-st * 45)
            + 0.35 * bandpass(rng.standard_normal(sn), 600, 3200) * np.exp(-st * 75)
        ) * 0.55
        out[i0 : i0 + sn] += step

    # Door handle latch click at t=2.25s + wooden door creak at t=2.40..3.20s
    ci = int(2.25 * SR)
    cn = int(0.08 * SR)
    cst = np.linspace(0, 0.08, cn, endpoint=False)
    out[ci : ci + cn] += np.sin(2 * np.pi * 1380 * cst) * np.exp(-cst * 65) * 0.65

    cr_m = ((t >= 2.40) & (t < 3.20)).astype(np.float32)
    crt = np.maximum(0, t - 2.40)
    f_cr = 310 + 45 * np.sin(2 * np.pi * 2.5 * crt)
    creak = (
        0.50 * np.sin(2 * np.pi * np.cumsum(f_cr) / SR)
        + 0.30 * np.sin(2 * np.pi * np.cumsum(f_cr * 2.0) / SR)
    ) * np.sin(np.pi * np.clip(crt / 0.80, 0, 1)) * cr_m * 0.38
    out += creak
    return out * 0.95, out * 1.05


def sfx_ticking_wall_clock(dur_s=5.0, rate_hz=1.0, with_room_hum=True):
    """
    Hypnotic mechanical office wall clock 'TICK ... TOCK ... TICK ... TOCK'.
    """
    n = int(dur_s * SR)
    t = np.linspace(0, dur_s, n, endpoint=False)
    rng = np.random.default_rng(404)
    out_l = np.zeros(n)
    out_r = np.zeros(n)

    if with_room_hum:
        hum = (0.12 * np.sin(2 * np.pi * 120 * t) + 0.06 * np.sin(2 * np.pi * 240 * t)) * 0.14
        out_l += hum
        out_r += hum

    num_ticks = int(dur_s * rate_hz * 2)
    for k in range(num_ticks):
        t0 = k * (0.5 / rate_hz) + 0.08
        i0 = int(t0 * SR)
        if i0 >= n - int(0.06 * SR):
            break
        tn = int(0.055 * SR)
        st = np.linspace(0, 0.055, tn, endpoint=False)
        # Alternating higher 'TICK' (1420 Hz) and lower 'TOCK' (1080 Hz)
        f_tick = 1420.0 if (k % 2 == 0) else 1080.0
        tick = (
            0.65 * np.sin(2 * np.pi * f_tick * st) * np.exp(-st * 95)
            + 0.35 * np.sin(2 * np.pi * (f_tick * 2.1) * st) * np.exp(-st * 130)
            + 0.30 * bandpass(rng.standard_normal(tn), 1000, 5500) * np.exp(-st * 140)
        ) * 0.62
        out_l[i0 : i0 + tn] += tick * 0.94
        out_r[i0 : i0 + tn] += tick * 1.06

    return out_l, out_r


def sfx_empty_gift_box_and_door():
    dur = 3.6
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    rng = np.random.default_rng(505)
    out = np.zeros(n)

    # Cardboard box lid pop & hollow resonance at t=0.75s
    bi = int(0.75 * SR)
    bn = int(0.28 * SR)
    bst = np.linspace(0, 0.28, bn, endpoint=False)
    pop = (
        0.60 * np.sin(2 * np.pi * (240 + 180 * (bst / 0.28)) * bst) * np.exp(-bst * 18)
        + 0.40 * bandpass(rng.standard_normal(bn), 500, 3200) * np.exp(-bst * 28)
    ) * 0.65
    out[bi : bi + bn] += pop

    # Door close click at t=2.85s
    di = int(2.85 * SR)
    dn = int(0.18 * SR)
    dst = np.linspace(0, 0.18, dn, endpoint=False)
    door_shut = (
        0.65 * np.sin(2 * np.pi * (120 * np.exp(-dst * 25)) * dst) * np.exp(-dst * 22)
        + 0.40 * np.sin(2 * np.pi * 980 * dst) * np.exp(-dst * 55)
    ) * 0.68
    out[di : di + dn] += door_shut
    return out * 0.95, out * 1.05


def sfx_paycheck_ping_and_paradise():
    dur = 4.0
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    out_l = np.zeros(n)
    out_r = np.zeros(n)

    # Phone vibrate buzz at t=0.15s + two-note payment chime ('+¥4,500') at t=0.35s & 0.50s
    vb_m = ((t >= 0.12) & (t < 0.32)).astype(np.float32)
    buzz = np.sin(2 * np.pi * 155 * t) * vb_m * 0.45
    out_l += buzz
    out_r += buzz

    for nt, nf in [(0.35, 1046.50), (0.50, 1567.98)]:
        ni = int(nt * SR)
        nn = int(0.55 * SR)
        nst = np.linspace(0, 0.55, nn, endpoint=False)
        ping = (
            0.60 * np.sin(2 * np.pi * nf * nst) * np.exp(-nst * 7.5)
            + 0.35 * np.sin(2 * np.pi * nf * 2 * nst) * np.exp(-nst * 11.0)
        ) * 0.62
        out_l[ni : ni + nn] += ping * 0.9
        out_r[ni : ni + nn] += ping * 1.1

    # Warm paradise sunbeam chord shimmer at t=2.2..3.9s
    p_m = ((t >= 2.20) & (t < 3.95)).astype(np.float32)
    pt = np.clip((t - 2.20) / 1.75, 0, 1)
    shimmer = (
        0.35 * np.sin(2 * np.pi * 523.25 * t)
        + 0.30 * np.sin(2 * np.pi * 659.25 * t)
        + 0.25 * np.sin(2 * np.pi * 783.99 * t)
        + 0.20 * np.sin(2 * np.pi * 987.77 * t)
    ) * np.sin(np.pi * pt) * p_m * 0.38
    out_l += shimmer * 0.92
    out_r += shimmer * 1.08
    return out_l, out_r


def sfx_calendar_flip_and_boss_peek():
    dur = 3.2
    n = int(dur * SR)
    rng = np.random.default_rng(843)
    out = np.zeros(n)

    # Rapid calendar tear-off flips ('NOV FRI 25')
    for ft in [0.10, 0.32, 0.54, 0.76, 0.98]:
        i0 = int(ft * SR)
        fn = int(0.16 * SR)
        st = np.linspace(0, 0.16, fn, endpoint=False)
        flap = bandpass(rng.standard_normal(fn), 900, 6200) * np.sin(np.pi * st / 0.16) ** 1.4 * 0.58
        out[i0 : i0 + fn] += flap

    # Comedic head-pop 'bloop' at t=1.55s
    pi = int(1.55 * SR)
    pn = int(0.22 * SR)
    pst = np.linspace(0, 0.22, pn, endpoint=False)
    f_pop = 320 + 480 * (pst / 0.22)
    out[pi : pi + pn] += np.sin(2 * np.pi * np.cumsum(f_pop) / SR) * np.exp(-pst * 18) * 0.55
    return out * 0.95, out * 1.05


def sfx_padlock_and_breaker_switches():
    """
    52.2s - 64.6s (12.4s finale):
    - t=1.8s (54.0s abs): Heavy brass padlock clank ('LABOR LAW')
    - t=4.4..7.2s (56.6..59.4s abs): 6 sharp industrial breaker switch CLACKS ('HOPE', 'A/C', 'LUNCH', 'WI-FI', 'WORK', 'FRIENDS')
    - t=8.5..12.3s (60.7..64.5s abs): Lonely echoing wall clock ticking in the dark room ('nobody can do nothing forever')
    """
    dur = 12.35
    n = int(dur * SR)
    rng = np.random.default_rng(1466)
    out_l = np.zeros(n)
    out_r = np.zeros(n)

    # 1. Heavy brass padlock clank at t=1.85s
    li = int(1.85 * SR)
    ln = int(0.32 * SR)
    lst = np.linspace(0, 0.32, ln, endpoint=False)
    lock_clank = (
        0.65 * np.sin(2 * np.pi * 1180 * lst) * np.exp(-lst * 22)
        + 0.45 * np.sin(2 * np.pi * 2460 * lst) * np.exp(-lst * 35)
        + 0.50 * np.sin(2 * np.pi * 185 * lst) * np.exp(-lst * 40)
    ) * 0.72
    out_l[li : li + ln] += lock_clank
    out_r[li : li + ln] += lock_clank

    # 2. 6 heavy breaker switch clacks (t=4.4, 4.95, 5.5, 6.05, 6.6, 7.15s)
    for sw_i, sw_t in enumerate([4.40, 4.95, 5.50, 6.05, 6.60, 7.15]):
        si = int(sw_t * SR)
        sn = int(0.11 * SR)
        sst = np.linspace(0, 0.11, sn, endpoint=False)
        f_sw = 920 - sw_i * 45
        clack = (
            0.70 * np.sin(2 * np.pi * f_sw * sst) * np.exp(-sst * 55)
            + 0.50 * np.sin(2 * np.pi * 165 * sst) * np.exp(-sst * 45)
            + 0.45 * bandpass(rng.standard_normal(sn), 800, 4800) * np.exp(-sst * 85)
        ) * 0.75
        out_l[si : si + sn] += clack * 0.95
        out_r[si : si + sn] += clack * 1.05

    # 3. Lonely echoing clock ticks at the end (t=8.5..12.3s)
    tl, tr = sfx_ticking_wall_clock(3.8, rate_hz=1.0, with_room_hum=True)
    ti = int(8.50 * SR)
    end = min(n, ti + len(tl))
    out_l[ti:end] += tl[: end - ti] * 1.15
    out_r[ti:end] += tr[: end - ti] * 1.15

    return out_l, out_r


def build_all():
    vo = read_vo(VO_WAV)
    total_samples = len(vo)
    dur_s = total_samples / SR
    print(f"Synthesizing 100% from-scratch SFX & Music stems for {dur_s:.4f}s ({total_samples} samples)...")

    sfx = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. Shots 01 & 02 (0.05 - 2.40s): Jammed 'FIRE EMPLOYEE' button & ejector seat
    l, r = sfx_jammed_fire_button()
    add_stereo(sfx, 0.05, l, r, gain=0.44)

    # 2. Shot 03 (2.60 - 4.40s): Boss dangling 'STORAGE' key
    l, r = sfx_storage_key_jingle(1.8)
    add_stereo(sfx, 2.60, l, r, gain=0.42)

    # 3. Shot 04 (4.65 - 8.05s): Office footsteps & opening 'CAREER DEVELOPMENT ROOM' door
    l, r = sfx_office_walk_and_door_open(3.4)
    add_stereo(sfx, 4.65, l, r, gain=0.42)

    # 4. Shots 05 & 06 (8.20 - 14.70s): Empty room hum & hypnotic ticking wall clock
    l, r = sfx_ticking_wall_clock(6.5, rate_hz=1.0, with_room_hum=True)
    add_stereo(sfx, 8.20, l, r, gain=0.46)

    # 5. Shot 07 (14.90 - 18.50s): Empty gift box lid pop & door shut
    l, r = sfx_empty_gift_box_and_door()
    add_stereo(sfx, 14.90, l, r, gain=0.44)

    # 6. Shot 08 (19.15 - 23.15s): '+¥4,500' paycheck chime & sunbeam paradise shimmer
    l, r = sfx_paycheck_ping_and_paradise()
    add_stereo(sfx, 19.15, l, r, gain=0.44)

    # 7. Shot 09 (23.60 - 29.60s): Coworkers staring & cobwebbed Inbox (0)
    l, r = sfx_ticking_wall_clock(6.0, rate_hz=0.8, with_room_hum=True)
    add_stereo(sfx, 23.60, l, r, gain=0.28)

    # 8. Shot 10 (29.95 - 33.15s): 'NOV FRI 25' calendar tear-off flips & Boss head pop
    l, r = sfx_calendar_flip_and_boss_peek()
    add_stereo(sfx, 29.95, l, r, gain=0.44)

    # 9. Shot 11 (35.40 - 45.40s): Ticking clock & relaxing tropical drink clink
    l, r = sfx_ticking_wall_clock(9.8, rate_hz=1.0, with_room_hum=True)
    add_stereo(sfx, 35.40, l, r, gain=0.35)

    # 10. Shot 12 (45.65 - 51.80s): Monday morning door open & eerie empty desk silence
    l, r = sfx_office_walk_and_door_open(2.8)
    add_stereo(sfx, 45.65, l, r, gain=0.38)

    # 11. Shot 13 (52.20 - 64.55s): Padlocked Labor Law alarm, 6 breaker switch clacks & lonely clock ticking
    l, r = sfx_padlock_and_breaker_switches()
    add_stereo(sfx, 52.20, l, r, gain=0.48)

    # Build Quirky-to-Psychological Corporate Suspense Music Stem (120 BPM, C minor -> Ab major -> Fm -> G7)
    t = np.linspace(0, dur_s, total_samples, endpoint=False)
    music = np.zeros((total_samples, 2), dtype=np.float32)

    roots = [65.41, 51.91, 87.31, 98.00]
    thirds = [77.78, 65.41, 103.83, 123.47]
    fifths = [98.00, 77.78, 130.81, 146.83]

    seg_len = 4.0
    num_segs = int(np.ceil(dur_s / seg_len))
    for s_idx in range(num_segs):
        t0 = s_idx * seg_len
        i0 = int(t0 * SR)
        i1 = min(total_samples, int((t0 + seg_len) * SR))
        if i1 <= i0:
            continue
        st = t[i0:i1] - t0
        f1 = roots[s_idx % 4]
        f2 = thirds[s_idx % 4]
        f3 = fifths[s_idx % 4]

        env = np.ones(i1 - i0)
        fade = min(int(0.25 * SR), (i1 - i0) // 4)
        if fade > 0:
            env[:fade] = np.linspace(0.3, 1.0, fade)
            env[-fade:] = np.linspace(1.0, 0.3, fade)

        pad_l = (
            0.42 * np.sin(2 * np.pi * f1 * st)
            + 0.30 * np.sin(2 * np.pi * f2 * 2 * st + 0.25)
            + 0.24 * np.sin(2 * np.pi * f3 * 2 * st + 0.65)
        ) * env
        pad_r = (
            0.42 * np.sin(2 * np.pi * f1 * st)
            + 0.30 * np.sin(2 * np.pi * f2 * 2 * st - 0.25)
            + 0.24 * np.sin(2 * np.pi * f3 * 2 * st - 0.65)
        ) * env

        # Marimba/plucked pizzicato clockwork pulse (4.0 Hz)
        pulse = (0.5 + 0.5 * np.sin(2 * np.pi * 4.0 * st - np.pi / 2)) ** 2.8
        pizz = np.sin(2 * np.pi * f1 * 4 * st) * pulse * 0.22 * env

        music[i0:i1, 0] += (pad_l + pizz * 0.95) * 0.15
        music[i0:i1, 1] += (pad_r + pizz * 1.05) * 0.15

    # Auto-duck music & sfx smoothly under speech
    vo_mono = np.abs(vo[:, 0])
    win = int(0.08 * SR)
    vo_env = np.convolve(vo_mono, np.ones(win) / win, mode="same")
    duck_music = np.clip(1.0 - vo_env * 2.4, 0.42, 1.0)[:, None]
    duck_sfx = np.clip(1.0 - vo_env * 1.05, 0.70, 1.0)[:, None]

    music_out = np.clip(music * duck_music, -0.98, 0.98)
    sfx_out = np.clip(sfx * duck_sfx, -0.98, 0.98)
    full_mix = np.clip(vo * 1.06 + sfx_out + music_out, -0.99, 0.99)

    write_wav_and_mp3(os.path.join(OUT_DIR, "Voiceover"), vo)
    write_wav_and_mp3(os.path.join(OUT_DIR, "SFX"), sfx_out)
    write_wav_and_mp3(os.path.join(OUT_DIR, "Music"), music_out)
    write_wav_and_mp3(os.path.join(OUT_DIR, "Full_Mixed_Audio"), full_mix)
    print("Successfully generated 100% from-scratch SFX, Music, Voiceover, and Full_Mixed_Audio (.wav & .mp3)!")


if __name__ == "__main__":
    build_all()
