import os
import wave
import subprocess
import numpy as np
from scipy import signal

SCRATCH_DIR = r"C:\Users\WayWe Work-Station\.gemini\antigravity\brain\8ad88795-d9fa-438b-8430-13b89b7ef998\scratch\railroad_project"
OUT_DIR = r"C:\Users\WayWe Work-Station\Downloads\Mate\Railroad Video"
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


def lowpass(sig, f_cut, order=4):
    nyq = 0.5 * SR
    b, a = signal.butter(order, min(nyq - 100.0, f_cut) / nyq, btype="low")
    return signal.lfilter(b, a, sig)


# ==============================================================================
# STUDIO-GRADE 100% FROM-SCRATCH PROCEDURAL FOLEY & SFX SYNTHESIZERS
# ==============================================================================

def sfx_hacksaw_on_steel_rail(dur_s=2.85):
    """
    Physical-modeling steel hacksaw cutting a railroad track:
    Alternating push (hard bite) and pull (lighter scrape) strokes at 2.8 Hz
    exciting steel rail modal frequencies (1180, 2420, 3890, 5240 Hz) + high-freq teeth grit.
    """
    n = int(dur_s * SR)
    t = np.linspace(0, dur_s, n, endpoint=False)
    rng = np.random.default_rng(3901)

    # 8 distinct back-and-forth saw strokes
    out_l = np.zeros(n)
    out_r = np.zeros(n)
    stroke_dur = 0.34
    for s_idx in range(int(dur_s / stroke_dur)):
        t0 = s_idx * stroke_dur
        i0 = int(t0 * SR)
        sn = min(int(stroke_dur * 0.88 * SR), n - i0)
        if sn <= 0:
            break
        st = np.linspace(0, sn / SR, sn, endpoint=False)
        is_push = (s_idx % 2 == 0)
        amp = 1.0 if is_push else 0.58
        pitch_shift = 1.0 if is_push else 1.12

        # Saw tooth impulse train (around 190 teeth/sec)
        tooth_rate = (210.0 if is_push else 175.0) * (1.0 - 0.15 * (st / (sn / SR)))
        tooth_phase = 2 * np.pi * np.cumsum(tooth_rate) / SR
        teeth = np.sin(tooth_phase) + 0.5 * np.sin(2 * tooth_phase)
        grit = bandpass(rng.standard_normal(sn), 1600, 6800) * (0.65 + 0.35 * teeth)

        # Steel rail ringing modes excited by saw
        modes = (
            0.35 * np.sin(2 * np.pi * 1180 * pitch_shift * st)
            + 0.28 * np.sin(2 * np.pi * 2420 * pitch_shift * st)
            + 0.22 * np.sin(2 * np.pi * 3890 * pitch_shift * st)
            + 0.15 * np.sin(2 * np.pi * 5240 * pitch_shift * st)
        )
        env = np.sin(np.pi * st / (sn / SR)) ** 1.3
        stroke_sig = (grit * 0.72 + modes * 0.45) * env * amp
        out_l[i0 : i0 + sn] += stroke_sig * 0.92
        out_r[i0 : i0 + sn] += stroke_sig * 1.08

    return out_l, out_r


def sfx_steam_locomotive_passby(dur_s=2.6, speed_hz=5.5, with_whistle=True):
    """
    Heavy 1880s steam locomotive roaring past with stereo Doppler pan,
    rhythmic cylinder steam chuffs, sub-bass wheel rumble, flange squeal, and 3-chime brass whistle.
    """
    n = int(dur_s * SR)
    t = np.linspace(0, dur_s, n, endpoint=False)
    rng = np.random.default_rng(707)

    # 4 chuffs per wheel revolution
    chuff_env = (0.5 + 0.5 * np.sin(2 * np.pi * speed_hz * t - np.pi / 2)) ** 2.8
    steam_noise = bandpass(rng.standard_normal(n), 280, 3800)
    chuffs = steam_noise * chuff_env * 0.85

    # Heavy iron wheel sub-bass rumble (52 Hz + 104 Hz + track clatter)
    rumble = (
        0.55 * np.sin(2 * np.pi * 52 * t)
        + 0.35 * np.sin(2 * np.pi * 104 * t)
        + 0.25 * lowpass(rng.standard_normal(n), 180)
    ) * 0.65

    # High-pitched steel wheel flange squeal
    squeal = (
        0.22 * np.sin(2 * np.pi * (2940 + 45 * np.sin(2 * np.pi * 6 * t)) * t)
        * np.sin(np.pi * t / dur_s) ** 2.0
    )

    sig = chuffs + rumble + squeal

    if with_whistle:
        # Doppler pitch curve (approaching 1.04x -> receding 0.93x)
        doppler = 1.04 - 0.11 * (1.0 / (1.0 + np.exp(-6.0 * (t - dur_s * 0.48))))
        w_mask = ((t >= 0.20) & (t <= dur_s - 0.35)).astype(np.float32)
        wt = np.clip((t - 0.20) / max(0.1, dur_s - 0.55), 0.0, 1.0)
        w_env = (np.sin(np.pi * wt) ** 0.7) * w_mask
        # 3-chime steam chord (D5=587.3, F#5=740.0, A5=880.0) + airy steam turbulence
        p1 = 2 * np.pi * np.cumsum(587.33 * doppler) / SR
        p2 = 2 * np.pi * np.cumsum(739.99 * doppler) / SR
        p3 = 2 * np.pi * np.cumsum(880.00 * doppler) / SR
        whistle = (
            0.38 * np.sin(p1)
            + 0.32 * np.sin(p2)
            + 0.28 * np.sin(p3)
            + 0.18 * np.sin(p1 * 2)
            + 0.22 * bandpass(rng.standard_normal(n), 1200, 4200)
        ) * w_env * 0.62
        sig += whistle

    env = np.sin(np.pi * t / dur_s) ** 0.85
    pan = np.linspace(0.22, 0.82, n)
    return sig * env * (1.0 - pan) * 1.4, sig * env * pan * 1.4


def sfx_canyon_wind_and_vertigo(dur_s=5.4):
    """
    Deep resonant canyon wind + steel scaffolding creak + vertigo sub-bass drop at t=4.0s.
    """
    n = int(dur_s * SR)
    t = np.linspace(0, dur_s, n, endpoint=False)
    rng = np.random.default_rng(303)

    w1 = bandpass(rng.standard_normal(n), 180, 620) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.38 * t))
    w2 = bandpass(rng.standard_normal(n), 450, 1250) * (0.45 + 0.45 * np.cos(2 * np.pi * 0.52 * t))

    # Vertigo sub-bass drop when camera tilts straight down into abyss (t=3.6..5.2s)
    v_mask = (t >= 3.5) & (t < 5.2)
    vt = np.maximum(0, t - 3.5)
    f_drop = 145.0 * np.exp(-vt * 1.1) + 36.0
    vertigo = np.sin(2 * np.pi * np.cumsum(f_drop) / SR) * np.exp(-vt * 0.9) * v_mask * 0.65

    env = np.sin(np.pi * t / dur_s) ** 0.8
    return (w1 * 0.9 + vertigo) * env * 0.55, (w2 * 0.9 + vertigo) * env * 0.55


def sfx_fast_zoom_whoosh(dur_s=1.25):
    n = int(dur_s * SR)
    t = np.linspace(0, dur_s, n, endpoint=False)
    rng = np.random.default_rng(505)
    noise = bandpass(rng.standard_normal(n), 150, 2600)
    f_sweep = 120 + 680 * np.sin(np.pi * t / dur_s) ** 1.8
    tone = np.sin(2 * np.pi * np.cumsum(f_sweep) / SR) * 0.45
    env = np.sin(np.pi * t / dur_s) ** 1.6
    sig = (noise * 0.85 + tone) * env
    return sig * 0.92, sig * 1.08


def sfx_gold_bullion_and_cash_bell():
    dur = 2.2
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    rng = np.random.default_rng(888)
    out_l = np.zeros(n)
    out_r = np.zeros(n)

    # Heavy gold bar thud + bright vintage cash register bell ('Cha-Ching!')
    bell_t = np.maximum(0, t - 0.12)
    bell_mask = (t >= 0.12).astype(np.float32)
    bell = (
        0.55 * np.sin(2 * np.pi * 2093.0 * bell_t) * np.exp(-bell_t * 4.5)
        + 0.40 * np.sin(2 * np.pi * 3135.96 * bell_t) * np.exp(-bell_t * 6.0)
        + 0.30 * np.sin(2 * np.pi * 4186.01 * bell_t) * np.exp(-bell_t * 8.5)
    ) * bell_mask * 0.55
    out_l += bell * 0.9
    out_r += bell * 1.1

    # Cascading gold coin pings
    for k in range(18):
        i0 = int(rng.uniform(0.05, 1.85) * SR)
        cn = int(0.16 * SR)
        st = np.linspace(0, 0.16, cn, endpoint=False)
        f = rng.uniform(2400, 4800)
        ping = (
            0.6 * np.sin(2 * np.pi * f * st)
            + 0.4 * np.sin(2 * np.pi * f * 1.48 * st)
        ) * np.exp(-st * 36)
        end = min(n, i0 + cn)
        pan = rng.uniform(0.25, 0.75)
        out_l[i0:end] += ping[: end - i0] * (1.0 - pan) * 0.42
        out_r[i0:end] += ping[: end - i0] * pan * 0.42

    return out_l, out_r


def sfx_gravel_footsteps_and_cane(dur_s=3.2):
    """
    Crunching river-pebble ballast footsteps + Boss tapping wooden cane on steel rail.
    """
    n = int(dur_s * SR)
    out = np.zeros(n)
    rng = np.random.default_rng(419)
    # 3 gravel crunch steps
    for st_t in [0.15, 0.68, 1.22]:
        i0 = int(st_t * SR)
        sn = int(0.18 * SR)
        st = np.linspace(0, 0.18, sn, endpoint=False)
        crunch = bandpass(rng.standard_normal(sn), 450, 4200) * np.sin(np.pi * st / 0.18) ** 1.4 * 0.65
        out[i0 : i0 + sn] += crunch
    # 2 sharp cane taps on steel rail
    for ct_t in [1.75, 2.35]:
        i0 = int(ct_t * SR)
        cn = int(0.14 * SR)
        st = np.linspace(0, 0.14, cn, endpoint=False)
        tap = (
            0.6 * np.sin(2 * np.pi * 1480 * st) * np.exp(-st * 45)
            + 0.4 * np.sin(2 * np.pi * 2960 * st) * np.exp(-st * 65)
            + 0.5 * bandpass(rng.standard_normal(cn), 800, 3500) * np.exp(-st * 80)
        ) * 0.75
        out[i0 : i0 + cn] += tap
    return out * 0.95, out * 1.05


def sfx_purple_boss_steam_kettle(dur_s=2.6):
    """
    Boss's face goes purple: high-pressure steam hiss + rising whistling kettle + cane slams!
    """
    n = int(dur_s * SR)
    t = np.linspace(0, dur_s, n, endpoint=False)
    rng = np.random.default_rng(516)

    hiss = bandpass(rng.standard_normal(n), 1200, 7500) * np.exp(-t * 1.1) * 0.75
    f_kettle = 1350 + 850 * (1.0 - np.exp(-t * 2.2))
    p_k = 2 * np.pi * np.cumsum(f_kettle) / SR
    kettle = (0.55 * np.sin(p_k) + 0.25 * np.sin(2 * p_k)) * np.exp(-t * 1.35) * np.sin(np.pi * np.clip(t / 0.15, 0, 1)) * 0.42
    sig = hiss + kettle
    return sig * 0.92, sig * 1.08


def sfx_rival_rail_weld_and_spikes(dur_s=4.2):
    """
    Rival company lays rails end-to-end: heavy mechanical rail clamp thud,
    4 ringing steel spike hammer blows, and sizzling electric welding sparks!
    """
    n = int(dur_s * SR)
    t = np.linspace(0, dur_s, n, endpoint=False)
    rng = np.random.default_rng(666)
    out = np.zeros(n)

    # 4 ringing steel spike hammer blows
    for hit_t in [0.25, 0.88, 1.52, 2.15]:
        i0 = int(hit_t * SR)
        hn = int(0.48 * SR)
        st = np.linspace(0, 0.48, hn, endpoint=False)
        clang = (
            0.65 * np.sin(2 * np.pi * 1240 * st) * np.exp(-st * 13)
            + 0.48 * np.sin(2 * np.pi * 2610 * st) * np.exp(-st * 20)
            + 0.35 * np.sin(2 * np.pi * 3980 * st) * np.exp(-st * 28)
            + 0.55 * np.sin(2 * np.pi * 135 * st) * np.exp(-st * 38)
        )
        out[i0 : min(n, i0 + hn)] += clang[: min(n, i0 + hn) - i0] * 0.68

    # Sizzling welding sparks (t=2.3..3.9s)
    w_mask = (t >= 2.30) & (t < 3.95)
    sizzle = bandpass(rng.standard_normal(n), 2800, 9500) * (rng.random(n) > 0.65) * w_mask * 0.55
    out += sizzle
    return out * 0.95, out * 1.05


def sfx_luxury_train_glide_and_teacup(dur_s=3.0):
    """
    Vandergold luxury parlor car gliding silently + delicate porcelain teacup clink.
    """
    n = int(dur_s * SR)
    t = np.linspace(0, dur_s, n, endpoint=False)
    glide = (
        0.35 * np.sin(2 * np.pi * 110 * t)
        + 0.25 * np.sin(2 * np.pi * 165 * t)
        + 0.15 * np.sin(2 * np.pi * 220 * t)
    ) * np.sin(np.pi * t / dur_s) * 0.28

    # Delicate porcelain teacup clink at t=1.1s
    ct = np.maximum(0, t - 1.10)
    cm = (t >= 1.10).astype(np.float32)
    cup = (
        0.45 * np.sin(2 * np.pi * 3450 * ct) * np.exp(-ct * 28)
        + 0.35 * np.sin(2 * np.pi * 5180 * ct) * np.exp(-ct * 42)
    ) * cm * 0.45
    sig = glide + cup
    return sig * 0.95, sig * 1.05


def sfx_clickety_clack_jolt(dur_s=3.1):
    """
    Signature hyper-active 'CLICKETY-CLACK! CLICKETY-CLACK!' wheel impacts over every rail gap
    + rattling wooden coach window + sloshing water in tin mug!
    """
    n = int(dur_s * SR)
    out_l = np.zeros(n)
    out_r = np.zeros(n)
    rng = np.random.default_rng(876)

    for cycle in range(5):
        base_t = cycle * 0.58 + 0.06
        # 4 wheel impacts per bogie pair ('click-e-ty-clack!')
        for sub_dt, f_ring, gain_h in [
            (0.00, 940.0, 0.85),
            (0.08, 1320.0, 0.70),
            (0.20, 880.0, 0.80),
            (0.28, 1210.0, 1.00),
        ]:
            i0 = int((base_t + sub_dt) * SR)
            if i0 >= n:
                continue
            cn = int(0.085 * SR)
            st = np.linspace(0, 0.085, cn, endpoint=False)
            # Heavy iron wheel thud + steel rail ring + wooden window rattle
            thud = np.sin(2 * np.pi * (175 * np.exp(-st * 35)) * st) * np.exp(-st * 40) * 0.75
            ring = (
                0.55 * np.sin(2 * np.pi * f_ring * st)
                + 0.35 * np.sin(2 * np.pi * f_ring * 1.62 * st)
            ) * np.exp(-st * 55)
            rattle = bandpass(rng.standard_normal(cn), 600, 4800) * np.exp(-st * 75) * 0.55
            hit = (thud + ring + rattle) * gain_h
            end = min(n, i0 + cn)
            out_l[i0:end] += hit[: end - i0] * 0.95
            out_r[i0:end] += hit[: end - i0] * 1.05

    return out_l, out_r


def sfx_newspaper_and_station(dur_s=4.5):
    """
    Crisp broadsheet newspaper snap + station clock bell + desert tumbleweed wind.
    """
    n = int(dur_s * SR)
    t = np.linspace(0, dur_s, n, endpoint=False)
    rng = np.random.default_rng(936)
    out = np.zeros(n)

    # Newspaper snap at t=0.15s and page rustle at t=1.10s
    for pt, pdur in [(0.15, 0.28), (1.10, 0.24)]:
        i0 = int(pt * SR)
        pn = int(pdur * SR)
        st = np.linspace(0, pdur, pn, endpoint=False)
        rustle = bandpass(rng.standard_normal(pn), 900, 6500) * np.sin(np.pi * st / pdur) ** 1.4 * 0.65
        out[i0 : i0 + pn] += rustle

    # Station brass clock bell at t=2.2s
    bt = np.maximum(0, t - 2.20)
    bm = (t >= 2.20).astype(np.float32)
    bell = (
        0.50 * np.sin(2 * np.pi * 659.25 * bt) * np.exp(-bt * 2.5)
        + 0.35 * np.sin(2 * np.pi * 1318.51 * bt) * np.exp(-bt * 4.0)
    ) * bm * 0.42
    out += bell

    # Tumbleweed dry brush & wind (t=2.8..4.4s)
    tw_m = ((t >= 2.8) & (t < 4.4)).astype(np.float32)
    brush = bandpass(rng.standard_normal(n), 400, 3200) * (0.5 + 0.5 * np.sin(2 * np.pi * 3.5 * t)) * tw_m * 0.28
    out += brush
    return out * 0.95, out * 1.05


def sfx_summer_thermometer_and_expansion():
    """
    41.2s - 53.3s (12.1s window):
    - t=0.3s: Rising thermometer mercury slide + desert heat shimmer
    - t=4.4s: Metallic rail expansion creak
    - t=7.85s (49.05s abs): Crisp silver coin clink into gap ('fit a coin in them')
    - t=9.2s: Calendar page tear-off flip ('JUNE' -> 'JULY')
    - t=10.45s (51.65s abs): Crisp sheet of paper slide into narrow gap ('barely a sheet of paper')
    """
    dur = 12.1
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    rng = np.random.default_rng(1880)
    out = np.zeros(n)

    # 1. Rising thermometer glass slide (t=0.25..1.45s)
    th_m = ((t >= 0.25) & (t < 1.45)).astype(np.float32)
    tht = np.clip((t - 0.25) / 1.20, 0, 1)
    f_th = 440.0 * (2.0 ** (tht * 1.2))
    out += np.sin(2 * np.pi * np.cumsum(f_th) / SR) * np.sin(np.pi * tht) * th_m * 0.32

    # 2. Subtle metallic rail expansion creaks (t=4.3..6.8s)
    cr_m = ((t >= 4.3) & (t < 6.8)).astype(np.float32)
    crt = np.maximum(0, t - 4.3)
    creak = (
        0.45 * np.sin(2 * np.pi * (165 + 25 * np.sin(2 * np.pi * 1.2 * crt)) * crt)
        + 0.30 * np.sin(2 * np.pi * 330 * crt)
    ) * np.sin(np.pi * np.clip(crt / 2.5, 0, 1)) * cr_m * 0.35
    out += creak

    # 3. Silver coin clink in May at t=7.85s (49.05s abs)
    ci = int(7.85 * SR)
    cn = int(0.35 * SR)
    cst = np.linspace(0, 0.35, cn, endpoint=False)
    coin = (
        0.60 * np.sin(2 * np.pi * 2950 * cst) * np.exp(-cst * 24)
        + 0.45 * np.sin(2 * np.pi * 4420 * cst) * np.exp(-cst * 35)
        + 0.35 * np.sin(2 * np.pi * 1680 * np.maximum(0, cst - 0.06)) * np.exp(-np.maximum(0, cst - 0.06) * 30) * (cst >= 0.06)
    ) * 0.72
    out[ci : ci + cn] += coin

    # 4. Calendar page tear flip at t=9.15s & paper sheet slide at t=10.45s
    for pt in [9.15, 10.45]:
        pi = int(pt * SR)
        pn = int(0.26 * SR)
        pst = np.linspace(0, 0.26, pn, endpoint=False)
        paper = bandpass(rng.standard_normal(pn), 1200, 7200) * np.sin(np.pi * pst / 0.26) ** 1.5 * 0.60
        out[pi : pi + pn] += paper

    return out * 0.95, out * 1.05


def sfx_groaning_rails_under_sun(dur_s=6.8):
    """
    57.0s - 63.8s: Deep, eerie metallic thermal groaning, stressed steel creaking,
    and popping fishplate bolts as the continuous rails push against each other!
    """
    n = int(dur_s * SR)
    t = np.linspace(0, dur_s, n, endpoint=False)
    rng = np.random.default_rng(1439)

    f_groan = 118.0 + 32.0 * np.sin(2 * np.pi * 0.42 * t) + 16.0 * np.cos(2 * np.pi * 0.95 * t)
    p_g = 2 * np.pi * np.cumsum(f_groan) / SR
    groan = (
        0.52 * np.sin(p_g)
        + 0.34 * np.sin(p_g * 2.01 + 0.4)
        + 0.24 * np.sin(p_g * 3.03 + 1.1)
        + 0.16 * np.sin(2 * np.pi * 485 * t + 3.5 * np.sin(2 * np.pi * 0.7 * t))
    )

    # Sharp metallic stress pings (strained bolts)
    pings = np.zeros(n)
    for pt, pf in [(1.1, 1650), (2.4, 1920), (3.8, 1780), (5.1, 2140)]:
        i0 = int(pt * SR)
        pn = int(0.22 * SR)
        st = np.linspace(0, 0.22, pn, endpoint=False)
        pings[i0 : i0 + pn] += np.sin(2 * np.pi * pf * st) * np.exp(-st * 28) * 0.45

    env = np.sin(np.pi * t / dur_s) ** 1.2
    sig = (groan * 0.75 + pings) * env * 0.62
    return sig * 0.94, sig * 1.06


def sfx_rail_gaps_click_shut():
    """
    67.4s - 69.5s: Two solid steel rail ends sliding together and locking flush ('Rail touching rail').
    """
    dur = 2.2
    n = int(dur * SR)
    out = np.zeros(n)
    for hit_t, f0 in [(0.15, 1120.0), (1.35, 1280.0)]:
        i0 = int(hit_t * SR)
        hn = int(0.32 * SR)
        st = np.linspace(0, 0.32, hn, endpoint=False)
        clack = (
            0.65 * np.sin(2 * np.pi * f0 * st) * np.exp(-st * 25)
            + 0.45 * np.sin(2 * np.pi * f0 * 1.85 * st) * np.exp(-st * 35)
            + 0.60 * np.sin(2 * np.pi * 155 * st) * np.exp(-st * 45)
        ) * 0.78
        out[i0 : i0 + hn] += clack
    return out * 0.95, out * 1.05


def sfx_snake_buckle_derail_and_explosion():
    """
    72.20s - 76.67s (4.47s finale):
    - t=0.18s (72.38s abs): Violent high-tension steel WHIP-SNAP as track kicks sideways like a snake
    - t=1.75s (73.95s abs): Piercing steel wheel derailment screech & bridge girder crunch
    - t=2.95s (75.15s abs): Colossal multi-layered canyon fireball explosion & shockwave!
    """
    dur = 4.46
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    rng = np.random.default_rng(1955)
    out_l = np.zeros(n)
    out_r = np.zeros(n)

    # 1. Steel snake whip-buckling snap (t=0.15..1.25s)
    w_mask = ((t >= 0.15) & (t < 1.25)).astype(np.float32)
    wt = np.maximum(0, t - 0.15)
    f_whip = 160.0 + 1150.0 * np.exp(-wt * 4.8)
    whip = (
        0.65 * np.sin(2 * np.pi * np.cumsum(f_whip) / SR) * np.exp(-wt * 3.5)
        + 0.45 * bandpass(rng.standard_normal(n), 800, 5200) * np.exp(-wt * 6.0)
    ) * w_mask * 0.88
    out_l += whip * 0.95
    out_r += whip * 1.05

    # 2. Derailment wheel screech & girder tear (t=1.70..2.95s)
    s_mask = ((t >= 1.70) & (t < 2.98)).astype(np.float32)
    st = np.maximum(0, t - 1.70)
    screech = (
        0.48 * np.sin(2 * np.pi * (2780 + 60 * np.sin(2 * np.pi * 16 * st)) * st)
        + 0.36 * np.sin(2 * np.pi * 3540 * st)
        + 0.40 * bandpass(rng.standard_normal(n), 500, 4200)
    ) * np.sin(np.pi * np.clip(st / 1.28, 0, 1)) * s_mask * 0.65
    out_l += screech * 0.92
    out_r += screech * 1.08

    # 3. Colossal canyon fireball explosion (t=2.95..4.46s)
    e_mask = (t >= 2.95).astype(np.float32)
    et = np.maximum(0, t - 2.95)
    # Sub-bass shockwave punch (95 Hz -> 28 Hz)
    sub_f = 95.0 * np.exp(-et * 2.8) + 28.0
    sub_boom = np.sin(2 * np.pi * np.cumsum(sub_f) / SR) * np.exp(-et * 1.35) * 1.15
    # Mid-range detonation crack & roaring fireball turbulence
    crack = bandpass(rng.standard_normal(n), 350, 4800) * np.exp(-et * 6.5) * 0.95
    fire_roar = lowpass(rng.standard_normal(n), 420) * np.exp(-et * 1.1) * 1.10
    debris = bandpass(rng.standard_normal(n), 900, 6200) * (rng.random(n) > 0.82) * np.exp(-et * 1.8) * 0.55

    blast_l = (sub_boom + crack + fire_roar * 0.95 + debris) * e_mask
    blast_r = (sub_boom + crack + fire_roar * 1.05 + debris) * e_mask
    out_l += blast_l
    out_r += blast_r

    return out_l, out_r


def build_all():
    vo = read_vo(VO_WAV)
    total_samples = len(vo)
    dur_s = total_samples / SR
    print(f"Synthesizing 100% from-scratch studio SFX & Music stems for {dur_s:.4f}s ({total_samples} samples)...")

    sfx = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. Shot 01 (0.08 - 2.93s): Steel hacksaw cutting 39-foot rail gap
    l, r = sfx_hacksaw_on_steel_rail(2.85)
    add_stereo(sfx, 0.08, l, r, gain=0.42)

    # 2. Shot 02 (2.95 - 5.45s): Steam Locomotive #7 roaring past with whistle
    l, r = sfx_steam_locomotive_passby(2.50, speed_hz=5.8, with_whistle=True)
    add_stereo(sfx, 2.95, l, r, gain=0.44)

    # 3. Shots 03 & 04 (4.85 - 10.20s): Deep canyon wind & vertigo abyss drop
    l, r = sfx_canyon_wind_and_vertigo(5.35)
    add_stereo(sfx, 4.85, l, r, gain=0.40)

    # 4. Shot 05 (10.15 - 11.40s): Fast desert dolly-zoom whoosh into Union Station
    l, r = sfx_fast_zoom_whoosh(1.25)
    add_stereo(sfx, 10.15, l, r, gain=0.42)

    # 5. Shot 06 (11.45 - 13.65s): Mountain of gold bars & '$' money sacks jingle
    l, r = sfx_gold_bullion_and_cash_bell()
    add_stereo(sfx, 11.45, l, r, gain=0.42)

    # 6. Shot 07 (13.80 - 15.80s): Canyon rim wind on high wooden beam
    l, r = sfx_canyon_wind_and_vertigo(2.0)
    add_stereo(sfx, 13.80, l, r, gain=0.28)

    # 7. Shot 08 (15.85 - 19.05s): Boss gravel footsteps & cane taps inspecting the rail gap
    l, r = sfx_gravel_footsteps_and_cane(3.2)
    add_stereo(sfx, 15.85, l, r, gain=0.40)

    # 8. Shot 09 (19.30 - 21.90s): Boss's face goes purple — steam ears whistle & hiss
    l, r = sfx_purple_boss_steam_kettle(2.6)
    add_stereo(sfx, 19.30, l, r, gain=0.42)

    # 9. Shot 11 (25.10 - 29.30s): Rival company spike hammer clangs & rail welding sparks
    l, r = sfx_rival_rail_weld_and_spikes(4.2)
    add_stereo(sfx, 25.10, l, r, gain=0.42)

    # 10. Shot 12 (29.95 - 32.95s): Vandergold luxury parlor car silent glide & teacup clink
    l, r = sfx_luxury_train_glide_and_teacup(3.0)
    add_stereo(sfx, 29.95, l, r, gain=0.38)

    # 11. Shot 13 (33.10 - 36.20s): Signature 'CLICKETY-CLACK!' jolting wooden coach
    l, r = sfx_clickety_clack_jolt(3.1)
    add_stereo(sfx, 33.10, l, r, gain=0.52)

    # 12. Shot 14 (36.25 - 40.75s): Newspaper snap, station clock bell & desert tumbleweed
    l, r = sfx_newspaper_and_station(4.5)
    add_stereo(sfx, 36.25, l, r, gain=0.40)

    # 13. Shots 15 & 16 (41.20 - 53.30s): Thermometer rise, silver coin in May & paper in July
    l, r = sfx_summer_thermometer_and_expansion()
    add_stereo(sfx, 41.20, l, r, gain=0.44)

    # 14. Shot 17 (53.40 - 56.60s): Thrilled Boss tapping cane on 39-FT rail tie
    l, r = sfx_gravel_footsteps_and_cane(3.2)
    add_stereo(sfx, 53.40, l, r, gain=0.38)

    # 15. Shot 18 (57.00 - 63.80s): Groaning steel rails under the afternoon sun
    l, r = sfx_groaning_rails_under_sun(6.8)
    add_stereo(sfx, 57.00, l, r, gain=0.42)

    # 16. Shot 19 (67.40 - 69.60s): Engineer's rail gaps clicking shut flush ('Rail touching rail')
    l, r = sfx_rail_gaps_click_shut()
    add_stereo(sfx, 67.40, l, r, gain=0.46)

    # 17. Shot 20 (70.15 - 76.67s): Approaching steam train + snake whip-buckle + derailment & fireball explosion!
    l, r = sfx_steam_locomotive_passby(2.2, speed_hz=6.2, with_whistle=True)
    add_stereo(sfx, 70.15, l, r, gain=0.42)

    l, r = sfx_snake_buckle_derail_and_explosion()
    add_stereo(sfx, 72.20, l, r, gain=0.54)

    # Build 100% from-scratch Western-Industrial Suspense Score (128 BPM, D minor -> Bb -> Gm -> A7)
    t = np.linspace(0, dur_s, total_samples, endpoint=False)
    music = np.zeros((total_samples, 2), dtype=np.float32)

    roots = [73.42, 58.27, 98.00, 110.00]
    thirds = [87.31, 73.42, 116.54, 138.59]
    fifths = [110.00, 87.31, 146.83, 164.81]

    seg_len = 3.75
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
            0.44 * np.sin(2 * np.pi * f1 * st)
            + 0.30 * np.sin(2 * np.pi * f2 * 2 * st + 0.3)
            + 0.24 * np.sin(2 * np.pi * f3 * 2 * st + 0.7)
        ) * env
        pad_r = (
            0.44 * np.sin(2 * np.pi * f1 * st)
            + 0.30 * np.sin(2 * np.pi * f2 * 2 * st - 0.3)
            + 0.24 * np.sin(2 * np.pi * f3 * 2 * st - 0.7)
        ) * env

        pulse = (0.5 + 0.5 * np.sin(2 * np.pi * 4.266 * st - np.pi / 2)) ** 2.4
        ost = np.sin(2 * np.pi * f1 * 2 * st) * pulse * 0.26 * env

        music[i0:i1, 0] += (pad_l + ost * 0.95) * 0.16
        music[i0:i1, 1] += (pad_r + ost * 1.05) * 0.16

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
