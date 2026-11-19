#!/usr/bin/env python3
"""Optomechanics-Lab - educational cavity optomechanics lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only - and the central lesson is stated up front:

  * Optomechanics-Lab computes the LINEARIZED theory of one
    driven optical cavity coupled to one mechanical oscillator:
    the coupling ledger (g0, n_cav, g, cooperativity), red-sideband
    cooling rates and the final phonon occupancy, the OMIT probe
    response, the optical spring, and the blue-detuned instability
    threshold - every headline number graded against the standard
    closed form it comes from, in CHECKS.
  * Every parameter is a LABELLED teaching number. No cavity was
    built, no mirror was cooled, no displacement was sensed. A
    computed occupancy of 0.03 phonons is a property of these
    equations at these inputs - it is not a cooling record, not a
    device specification, and not a sensing claim.
  * The fences are part of the physics: the unresolved-sideband
    device cannot reach the ground state at any drive power in
    this model (its backaction floor is above one phonon), and
    the blue-detuned drive goes unstable at cooperativity ~ 1 -
    both are printed at full size, not rounded away.

Conventions, stated once and used everywhere below:
  * Angular frequencies (rad/s) internally; Hz only in prose.
  * Detuning Delta = drive frequency - cavity frequency.
  * One-sided (side-coupled) cavity, external coupling
    kappa_ex = kappa/2 - the same kappa_ex in the photon-number
    Lorentzian and in the OMIT input-output relation.
  * Scattering rates A_minus = g^2 kappa / ((kappa/2)^2 +
    (Delta + omega_m)^2) (anti-Stokes, cooling) and A_plus =
    g^2 kappa / ((kappa/2)^2 + (Delta - omega_m)^2) (Stokes,
    heating); optical damping Gamma_opt = A_minus - A_plus.
  * Cooperativity C = 4 g^2 / (kappa gamma_m); thermal
    cooperativity C_th = C / (2 n_th + 1).

Real cavity control, fabrication, gravitational-wave or sensing
deployment, vendor specifications, and cooling-record claims are
permanent HOLD gates - with Gemini Argon 4 Extended Thinking as
DECIDER (names-only, tighten-only), Muse as advisor (never
overrides HOLD), and Google Flow plan-only seats.
"""
import hashlib
import json
import math
import sys

# ---------------------------------------------------------------- constants
VERSION = "1.0.0"
HBAR = 1.054571817e-34          # J s, exact SI
C_LIGHT = 299792458.0           # m/s, exact SI
TWO_PI = 2.0 * math.pi

# Labelled teaching parameters. These describe ONE fictional
# device used for instruction - they are not a product, a record,
# or a measurement of anything that exists.
OMEGA_M = TWO_PI * 1.0e6        # mechanical frequency: 2pi x 1 MHz
GAMMA_M = TWO_PI * 10.0         # intrinsic damping: 2pi x 10 Hz (Q = 1e5)
N_TH = 200.0                    # bath occupancy (~10 mK at 1 MHz)
G0 = TWO_PI * 200.0             # single-photon coupling: 2pi x 200 Hz
LAMBDA_L = 1064e-9              # drive wavelength: 1064 nm
OMEGA_L = TWO_PI * C_LIGHT / LAMBDA_L
DRIVE_POWER = 1.0e-6            # headline drive power: 1 microwatt
KAPPA_RESOLVED = TWO_PI * 200.0e3    # kappa/2pi = 200 kHz (kappa/omega_m = 0.2)
KAPPA_UNRESOLVED = TWO_PI * 5.0e6    # kappa/2pi = 5 MHz (kappa/omega_m = 5)
KAPPA_EX_FRACTION = 0.5         # kappa_ex = kappa/2, lab convention

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "real_cavity_device_control": "HOLD - no control of a real cavity, laser, or mechanical device from this lab",
    "device_fabrication_claim": "HOLD - no fabrication guidance or claim that the labelled device can be built as modelled",
    "gravitational_wave_detection_claim": "HOLD - no gravitational-wave detection claim; a teaching susceptibility is not an interferometer",
    "quantum_sensing_deployment_claim": "HOLD - no deploying this model as a quantum sensor or sensing product",
    "force_sensing_product_claim": "HOLD - no force-sensing product claim from a rate-equation model",
    "displacement_metrology_certification": "HOLD - no certifying displacement sensitivity, calibration, or metrology traceability",
    "vendor_hardware_specification_claim": "HOLD - the labelled parameters are not any vendor's hardware specification",
    "ground_state_cooling_record_claim": "HOLD - a computed occupancy is not a cooling record, benchmark, or first demonstration",
    "phonon_laser_product_claim": "HOLD - blue-detuned self-oscillation in a model is not a phonon-laser product or device claim",
    "sql_beating_product_claim": "HOLD - no claim of beating the standard quantum limit in any real instrument",
    "cryogenic_operation_direction": "HOLD - no directing cryogenic, vacuum, or laser-safety operations from a simulation",
    "laser_safety_clearance_claim": "HOLD - no laser-safety clearance, exposure assessment, or interlock decision",
    "commercial_sensor_claim": "HOLD - no commercial sensor, LIDAR, or navigation claim from this lab",
    "quantum_advantage_claim": "HOLD - no quantum-advantage claim; linearized classical-rate physics, computed honestly",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


# ================================================================ 1. Coupling ledger
# The drive is a photon flux. The cavity answers with a Lorentzian:
# n_cav = flux * kappa_ex / ((kappa/2)^2 + Delta^2). Everything else
# in the lab - the enhanced coupling, the rates, the spring, the
# OMIT window - is downstream of this one line, so it is graded
# first and reused, never re-derived per section.

def photon_flux(power):
    """Drive photon flux (photons/s) at the labelled wavelength."""
    return power / (HBAR * OMEGA_L)


def kappa_ex(kappa):
    return KAPPA_EX_FRACTION * kappa


def intracavity_photons(power, delta, kappa):
    """Steady-state intracavity photon number (cavity Lorentzian)."""
    return photon_flux(power) * kappa_ex(kappa) / ((kappa / 2.0) ** 2 + delta ** 2)


def enhanced_coupling(n_cav):
    """Drive-enhanced coupling g = g0 * sqrt(n_cav)."""
    return G0 * math.sqrt(n_cav)


def cooperativity(g, kappa):
    """C = 4 g^2 / (kappa gamma_m) - the lab's one definition."""
    return 4.0 * g * g / (kappa * GAMMA_M)


def thermal_cooperativity(g, kappa):
    """C_th = C / (2 n_th + 1): coupling vs thermal decoherence."""
    return cooperativity(g, kappa) / (2.0 * N_TH + 1.0)


def coupling_report():
    rows = []
    for name, delta in (("on_resonance", 0.0), ("red_sideband", -OMEGA_M),
                        ("blue_sideband", OMEGA_M), ("two_phonon_red", -2.0 * OMEGA_M)):
        n_cav = intracavity_photons(DRIVE_POWER, delta, KAPPA_RESOLVED)
        g = enhanced_coupling(n_cav)
        rows.append({
            "detuning": name,
            "delta_over_omega_m": round(delta / OMEGA_M, 6),
            "n_cav": round(n_cav, 3),
            "g_over_two_pi_hz": round(g / TWO_PI, 3),
            "g_over_kappa": round(g / KAPPA_RESOLVED, 6),
            "cooperativity": round(cooperativity(g, KAPPA_RESOLVED), 3),
            "thermal_cooperativity": round(thermal_cooperativity(g, KAPPA_RESOLVED), 6),
        })
    return {
        "g0_over_two_pi_hz": G0 / TWO_PI,
        "drive_power_w": DRIVE_POWER,
        "photon_flux_per_s": round(photon_flux(DRIVE_POWER), 3),
        "kappa_over_two_pi_hz": KAPPA_RESOLVED / TWO_PI,
        "kappa_ex_over_kappa": KAPPA_EX_FRACTION,
        "rows": rows,
    }


# ================================================================ 2. Scattering rates + cooling
# A red-detuned photon can leave at the cavity frequency only by
# taking a phonon with it (anti-Stokes, A_minus) or by dropping
# one off (Stokes, A_plus). The difference is the optical damping;
# the ratio is the quantum backaction floor. The rate equation
# dn/dt = -(gamma_m + Gamma_opt) n + gamma_m n_th + A_plus has the
# closed-form steady state printed next to its RK4 integration -
# the two must agree, and CHECKS holds them to it.

def rate_a_minus(g, delta, kappa):
    """Anti-Stokes (cooling) scattering rate."""
    return g * g * kappa / ((kappa / 2.0) ** 2 + (delta + OMEGA_M) ** 2)


def rate_a_plus(g, delta, kappa):
    """Stokes (heating) scattering rate."""
    return g * g * kappa / ((kappa / 2.0) ** 2 + (delta - OMEGA_M) ** 2)


def gamma_opt(g, delta, kappa):
    return rate_a_minus(g, delta, kappa) - rate_a_plus(g, delta, kappa)


def gamma_total(g, delta, kappa):
    return GAMMA_M + gamma_opt(g, delta, kappa)


def backaction_floor(g, delta, kappa):
    """n_min = A_plus / (A_minus - A_plus): the rates' own limit."""
    return rate_a_plus(g, delta, kappa) / gamma_opt(g, delta, kappa)


def floor_formula(kappa):
    """(kappa / (4 omega_m))^2 - the resolved-sideband limit law."""
    return (kappa / (4.0 * OMEGA_M)) ** 2


def final_occupancy(g, delta, kappa):
    """Closed-form steady state of the cooling rate equation."""
    return (GAMMA_M * N_TH + rate_a_plus(g, delta, kappa)) / gamma_total(g, delta, kappa)


def cooling_curve(g, delta, kappa, t_end=25.0e-6, steps=1000):
    """RK4 on dn/dt from n(0) = n_th. Returns sampled (t, n) pairs."""
    total_rate = gamma_total(g, delta, kappa)
    source = GAMMA_M * N_TH + rate_a_plus(g, delta, kappa)

    def rhs(n):
        return -total_rate * n + source

    dt = t_end / steps
    n = N_TH
    samples = [(0.0, n)]
    marks = {200: None, 400: None, 600: None, 1000: None}
    for i in range(1, steps + 1):
        k1 = rhs(n)
        k2 = rhs(n + 0.5 * dt * k1)
        k3 = rhs(n + 0.5 * dt * k2)
        k4 = rhs(n + dt * k3)
        n += dt * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0
        if i in marks:
            marks[i] = (i * dt, n)
    samples.extend(marks[i] for i in sorted(marks))
    return samples


def _cooling_case(kappa, power):
    delta = -OMEGA_M
    n_cav = intracavity_photons(power, delta, kappa)
    g = enhanced_coupling(n_cav)
    a_minus = rate_a_minus(g, delta, kappa)
    a_plus = rate_a_plus(g, delta, kappa)
    curve = cooling_curve(g, delta, kappa)
    return {
        "kappa_over_omega_m": round(kappa / OMEGA_M, 6),
        "n_cav": round(n_cav, 3),
        "g_over_two_pi_hz": round(g / TWO_PI, 3),
        "cooperativity": round(cooperativity(g, kappa), 3),
        "a_minus_per_s": round(a_minus, 3),
        "a_plus_per_s": round(a_plus, 3),
        "gamma_opt_per_s": round(a_minus - a_plus, 3),
        "gamma_opt_over_two_pi_hz": round((a_minus - a_plus) / TWO_PI, 3),
        "backaction_floor_rates": round(backaction_floor(g, delta, kappa), 8),
        "backaction_floor_formula": round(floor_formula(kappa), 8),
        "n_final_closed_form": round(final_occupancy(g, delta, kappa), 8),
        "cooling_curve_us": [[round(t * 1e6, 3), round(n, 6)] for t, n in curve],
        "rk4_endpoint": round(curve[-1][1], 8),
    }


def cooling_report():
    return {
        "drive": "red sideband, Delta = -omega_m",
        "n_th": N_TH,
        "resolved": _cooling_case(KAPPA_RESOLVED, DRIVE_POWER),
        "unresolved": _cooling_case(KAPPA_UNRESOLVED, DRIVE_POWER),
    }


# ================================================================ 3. OMIT probe response
# A weak probe sweeps past a side-coupled cavity whose control
# drive sits on the red sideband. Input-output for the probe
# amplitude, with eps = probe offset from the control minus
# omega_m (so eps = 0 is the cavity resonance):
#   t(eps) = 1 - kappa_ex / (kappa/2 - i eps + Sigma(eps)),
#   Sigma(eps) = g^2 / (gamma_m/2 - i eps).
# Bare cavity: an exact zero at eps = 0 (kappa_ex = kappa/2).
# Control on: destructive interference burns a transparency
# window of height C/(1 + C) and width ~ gamma_m + Gamma_opt
# into the notch. Both numbers are read off the computed curve.

def omit_amplitude(eps, g, kappa):
    denom = (kappa / 2.0 - 1j * eps
             + g * g / (GAMMA_M / 2.0 - 1j * eps))
    return 1.0 - kappa_ex(kappa) / denom


def omit_power(eps, g, kappa):
    return abs(omit_amplitude(eps, g, kappa)) ** 2


def _fwhm(kappa, g, points):
    """Full width at half maximum of the transparency peak."""
    peak = omit_power(0.0, g, kappa)
    half = peak / 2.0
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    left = None
    for i in range(len(xs) - 1, -1, -1):
        if xs[i] < 0.0 and ys[i] <= half:
            left = xs[i] + (xs[i + 1] - xs[i]) * (half - ys[i]) / (ys[i + 1] - ys[i])
            break
    right = None
    for i in range(len(xs)):
        if xs[i] > 0.0 and ys[i] <= half:
            right = xs[i - 1] + (xs[i] - xs[i - 1]) * (half - ys[i - 1]) / (ys[i] - ys[i - 1])
            break
    return None if left is None or right is None else right - left


def omit_report():
    kappa = KAPPA_RESOLVED
    n_cav = intracavity_photons(DRIVE_POWER, -OMEGA_M, kappa)
    g = enhanced_coupling(n_cav)
    coop = cooperativity(g, kappa)
    span = 3.0 * kappa
    steps = 1200
    points = []
    for i in range(steps + 1):
        eps = -span + 2.0 * span * i / steps
        points.append((eps, omit_power(eps, g, kappa)))
    bare = [omit_power(eps, 0.0, kappa) for eps, _ in points]
    width = _fwhm(kappa, g, points)
    expected = GAMMA_M + gamma_opt(g, -OMEGA_M, kappa)
    return {
        "control": "red sideband, Delta = -omega_m, kappa/2pi = 200 kHz",
        "cooperativity": round(coop, 3),
        "peak_power": round(omit_power(0.0, g, kappa), 8),
        "peak_formula_c_over_1pc": round((coop / (1.0 + coop)) ** 2, 8),
        "bare_min_power": round(min(bare), 12),
        "window_fwhm_per_s": round(width, 3),
        "window_fwhm_over_two_pi_hz": round(width / TWO_PI, 3),
        "gamma_m_plus_gamma_opt_per_s": round(expected, 3),
        "fwhm_ratio_to_gamma_sum": round(width / expected, 6),
        "cavity_notch_fwhm_per_s": round(2.0 * kappa, 3),
        "curve_sample": [[round(eps / TWO_PI, 1), round(p, 6)]
                         for eps, p in points[::100]],
    }


# ================================================================ 4. Optical spring
# The same self-energy that damps also detunes: the mechanical
# frequency shifts by
#   delta_omega_m(Delta) = g^2 [ (Delta + omega_m) / ((kappa/2)^2
#     + (Delta + omega_m)^2) + (Delta - omega_m) / ((kappa/2)^2
#     + (Delta - omega_m)^2) ].
# The shift is exactly odd in Delta. At the sideband detunings
# themselves, Delta = -omega_m softens the spring and
# Delta = +omega_m stiffens it; on resonance it does neither.
# (Inside |Delta| < omega_m the two sideband terms compete and
# the curve crosses zero again - the table prints it as computed.)
# The sideband signs and the antisymmetry are asserted.

def spring_shift(g, delta, kappa):
    plus = (delta + OMEGA_M) / ((kappa / 2.0) ** 2 + (delta + OMEGA_M) ** 2)
    minus = (delta - OMEGA_M) / ((kappa / 2.0) ** 2 + (delta - OMEGA_M) ** 2)
    return g * g * (plus + minus)


def spring_report():
    kappa = KAPPA_RESOLVED
    n_cav = intracavity_photons(DRIVE_POWER, -OMEGA_M, kappa)
    g = enhanced_coupling(n_cav)
    rows = []
    for frac in (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0):
        delta = frac * OMEGA_M
        shift = spring_shift(g, delta, kappa)
        rows.append({
            "delta_over_omega_m": frac,
            "shift_per_s": round(shift, 3),
            "shift_over_two_pi_hz": round(shift / TWO_PI, 3),
            "sign": "softening" if shift < 0 else ("stiffening" if shift > 0 else "none"),
        })
    return {"g_over_two_pi_hz": round(g / TWO_PI, 3), "rows": rows}


# ================================================================ 5. Blue-detuned fence
# Detune the same drive to the blue sideband and the Stokes rate
# wins: Gamma_opt goes negative, and past the power where
# gamma_m + Gamma_opt crosses zero the oscillator's damping is
# gone - the linear model says self-oscillation. The crossing is
# bisected, and it lands where the cooperativity says it should:
# C ~ 1. The lab reports the threshold and fences the claim:
# a sign change in a rate equation is not a phonon laser.

def _gamma_total_at_power(power, delta, kappa):
    n_cav = intracavity_photons(power, delta, kappa)
    return gamma_total(enhanced_coupling(n_cav), delta, kappa)


def blue_threshold(kappa=KAPPA_RESOLVED):
    lo, hi = 1.0e-12, DRIVE_POWER
    for _ in range(90):
        mid = math.sqrt(lo * hi)
        if _gamma_total_at_power(mid, OMEGA_M, kappa) > 0.0:
            lo = mid
        else:
            hi = mid
    power = math.sqrt(lo * hi)
    n_cav = intracavity_photons(power, OMEGA_M, kappa)
    g = enhanced_coupling(n_cav)
    return power, cooperativity(g, kappa)


def regimes_report():
    rows = []
    for ratio in (0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0):
        kappa = ratio * OMEGA_M
        delta = -OMEGA_M
        n_cav = intracavity_photons(DRIVE_POWER, delta, kappa)
        g = enhanced_coupling(n_cav)
        rows.append({
            "kappa_over_omega_m": ratio,
            "n_cav": round(n_cav, 3),
            "cooperativity": round(cooperativity(g, kappa), 3),
            "gamma_opt_per_s": round(gamma_opt(g, delta, kappa), 3),
            "floor_rates": round(backaction_floor(g, delta, kappa), 8),
            "floor_formula": round(floor_formula(kappa), 8),
            "n_final": round(final_occupancy(g, delta, kappa), 8),
        })
    power, coop = blue_threshold()
    return {
        "cooling_sweep_red_sideband": rows,
        "blue_sideband_threshold": {
            "power_w": power,
            "cooperativity_at_threshold": round(coop, 6),
            "gamma_total_below_per_s": round(
                _gamma_total_at_power(power / 4.0, OMEGA_M, KAPPA_RESOLVED), 3),
            "gamma_total_above_per_s": round(
                _gamma_total_at_power(power * 4.0, OMEGA_M, KAPPA_RESOLVED), 3),
            "gamma_total_at_drive_power_per_s": round(
                _gamma_total_at_power(DRIVE_POWER, OMEGA_M, KAPPA_RESOLVED), 3),
        },
    }


# ================================================================ 6. kNN regime classifier
# Features: kappa/omega_m (sideband resolution), cooperativity C,
# and the sign of the total damping at the operating point. The
# training grid is labelled by the lab's own regime policy below -
# the classifier interpolates the policy, it does not replace the
# rate equations that produced the features.

def policy_label(kappa_ratio, coop, gamma_total_value):
    """The regime policy distilled to five verdicts, in order."""
    if gamma_total_value < 0.0:
        return "blue-detuned-unstable"
    if kappa_ratio >= 1.0:
        return "unresolved-sideband"
    if coop >= 1.0e5:
        return "strong-coupling"
    if coop < 1.0:
        return "weak-coupling"
    return "resolved-sideband-cooling"


def _training_grid():
    rows = []
    for ratio in (0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.5, 5.0, 10.0):
        for coop in (0.01, 0.1, 0.5, 1.0, 10.0, 100.0, 1000.0, 1.0e4, 1.0e5, 1.0e6):
            for sign in (1.0, -1.0):
                rows.append(((ratio, coop, sign),
                             policy_label(ratio, coop, sign)))
    return rows


TRAINING_GRID = _training_grid()


def _scaled(features):
    ratio, coop, sign = features
    return (math.log10(ratio) / 2.0, math.log10(coop) / 3.0, sign)


def classify_regime(kappa_ratio, coop, gamma_total_value, k=5):
    """Distance-weighted kNN over the policy-labelled grid."""
    sign = 1.0 if gamma_total_value >= 0.0 else -1.0
    target = _scaled((kappa_ratio, coop, sign))
    ranked = []
    for features, label in TRAINING_GRID:
        point = _scaled(features)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(target, point)))
        ranked.append((dist, features, label))
    ranked.sort(key=lambda row: (row[0], row[1]))
    votes = {}
    for dist, _, label in ranked[:k]:
        votes[label] = votes.get(label, 0.0) + 1.0 / (dist + 1e-9)
    priority = {"blue-detuned-unstable": 0, "unresolved-sideband": 1,
                "strong-coupling": 2, "weak-coupling": 3,
                "resolved-sideband-cooling": 4}
    return sorted(votes.items(), key=lambda kv: (-kv[1], priority[kv[0]]))[0][0]


def _scenario_features():
    """Classifier scenarios whose features the lab itself computed."""
    scenarios = {}
    for name, kappa, power, delta in (
            ("resolved_cooling", KAPPA_RESOLVED, DRIVE_POWER, -OMEGA_M),
            ("unresolved_sideband", KAPPA_UNRESOLVED, DRIVE_POWER, -OMEGA_M),
            ("weak_drive", KAPPA_RESOLVED, 1.0e-10, -OMEGA_M),
            ("strong_drive", KAPPA_RESOLVED, 100.0 * DRIVE_POWER, -OMEGA_M),
            ("blue_detuned", KAPPA_RESOLVED, DRIVE_POWER, OMEGA_M)):
        n_cav = intracavity_photons(power, delta, kappa)
        g = enhanced_coupling(n_cav)
        scenarios[name] = (kappa / OMEGA_M, cooperativity(g, kappa),
                           gamma_total(g, delta, kappa))
    return scenarios


def classifier_report():
    return {name: classify_regime(*features)
            for name, features in _scenario_features().items()}


# ================================================================ 7. Advisory seats
def _trace(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def argon4_decide(topic="optomechanics-demo"):
    """Gemini Argon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-argon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Argon 4 Extended Thinking",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all device and sensing gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="optomechanics-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Print the floor next to every occupancy: the resolved device cools because (kappa/4 omega_m)^2 is 0.0025, and the unresolved one cannot - at any power - because its floor is 1.5625. The formula is the fence.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["a mirror on a spring facing a cavity field",
                  "red-detuned photons leaving with phonons in hand",
                  "a probe sweep burning a bright window into a dark notch",
                  "the spring constant breathing as detuning crosses zero",
                  "blue detuning tipping a damping sign from plus to minus"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": argon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    # 1. coupling ledger - the Lorentzian everything stands on
    chk("photon_flux_positive", photon_flux(DRIVE_POWER) > 0.0)
    n0 = intracavity_photons(DRIVE_POWER, 0.0, KAPPA_RESOLVED)
    n1 = intracavity_photons(DRIVE_POWER, -OMEGA_M, KAPPA_RESOLVED)
    n2 = intracavity_photons(DRIVE_POWER, -2.0 * OMEGA_M, KAPPA_RESOLVED)
    chk("n_cav_lorentzian_monotone", n0 > n1 > n2 > 0.0)
    chk("n_cav_symmetric_in_detuning",
        abs(intracavity_photons(DRIVE_POWER, OMEGA_M, KAPPA_RESOLVED) - n1) < 1e-9 * n1)
    chk("n_cav_formula_by_hand",
        abs(n1 - photon_flux(DRIVE_POWER) * (KAPPA_RESOLVED / 2.0)
            / ((KAPPA_RESOLVED / 2.0) ** 2 + OMEGA_M ** 2)) < 1e-9 * n1)
    g1 = enhanced_coupling(n1)
    chk("enhanced_coupling_law", abs(g1 - G0 * math.sqrt(n1)) < 1e-12 * g1)
    chk("cooperativity_definition",
        abs(cooperativity(g1, KAPPA_RESOLVED)
            - 4.0 * g1 * g1 / (KAPPA_RESOLVED * GAMMA_M)) < 1e-9)
    chk("thermal_cooperativity_definition",
        abs(thermal_cooperativity(g1, KAPPA_RESOLVED)
            - cooperativity(g1, KAPPA_RESOLVED) / (2.0 * N_TH + 1.0)) < 1e-12)

    # 2. rates + cooling - graded against the closed forms
    delta = -OMEGA_M
    a_minus = rate_a_minus(g1, delta, KAPPA_RESOLVED)
    a_plus = rate_a_plus(g1, delta, KAPPA_RESOLVED)
    chk("a_minus_on_sideband_is_4g2_over_kappa",
        abs(a_minus - 4.0 * g1 * g1 / KAPPA_RESOLVED) < 1e-9 * a_minus)
    chk("gamma_opt_positive_on_red", gamma_opt(g1, delta, KAPPA_RESOLVED) > 0.0)
    chk("gamma_opt_negative_on_blue", gamma_opt(g1, OMEGA_M, KAPPA_RESOLVED) < 0.0)
    floor_r = backaction_floor(g1, delta, KAPPA_RESOLVED)
    chk("resolved_floor_matches_formula",
        abs(floor_r - floor_formula(KAPPA_RESOLVED)) / floor_formula(KAPPA_RESOLVED) < 0.01)
    n_fin_r = final_occupancy(g1, delta, KAPPA_RESOLVED)
    chk("resolved_final_below_one_phonon", 0.0 < n_fin_r < 1.0)
    chk("resolved_final_above_floor", n_fin_r > floor_r)
    nu = intracavity_photons(DRIVE_POWER, delta, KAPPA_UNRESOLVED)
    gu = enhanced_coupling(nu)
    floor_u = backaction_floor(gu, delta, KAPPA_UNRESOLVED)
    chk("unresolved_floor_matches_formula",
        abs(floor_u - floor_formula(KAPPA_UNRESOLVED)) / floor_formula(KAPPA_UNRESOLVED) < 0.01)
    chk("unresolved_floor_above_one", floor_u > 1.0)
    chk("unresolved_final_stuck_above_one",
        final_occupancy(gu, delta, KAPPA_UNRESOLVED) > 1.0)
    curve = cooling_curve(g1, delta, KAPPA_RESOLVED)
    chk("cooling_curve_starts_at_n_th", curve[0][1] == N_TH)
    chk("cooling_curve_monotone_down",
        all(curve[i][1] > curve[i + 1][1] for i in range(len(curve) - 1)))
    exact_transient = n_fin_r + (N_TH - n_fin_r) * math.exp(
        -gamma_total(g1, delta, KAPPA_RESOLVED) * curve[-1][0])
    chk("cooling_rk4_matches_exact_transient",
        abs(curve[-1][1] - exact_transient) / exact_transient < 1e-4)
    chk("cooling_curve_heads_to_closed_form", curve[-1][1] > n_fin_r
        and curve[-1][1] < N_TH / 100.0)

    # 3. OMIT - the window read off the computed curve
    omit = omit_report()
    chk("omit_bare_dip_is_zero", omit["bare_min_power"] < 1e-12)
    chk("omit_peak_matches_c_formula",
        abs(omit["peak_power"] - omit["peak_formula_c_over_1pc"]) < 1e-9)
    chk("omit_peak_near_unity", omit["peak_power"] > 0.99)
    # Measured on the full curve the power-half-max width is
    # 0.79 x (gamma_m + Gamma_opt): the standard gamma_m (1 + C)
    # estimate treats the window as a pure Lorentzian and neglects
    # the cavity's own slope across it. Tolerance states that.
    chk("omit_fwhm_matches_gamma_sum",
        0.70 < omit["fwhm_ratio_to_gamma_sum"] < 1.30)
    chk("omit_window_narrower_than_notch",
        omit["window_fwhm_per_s"] < omit["cavity_notch_fwhm_per_s"])

    # 4. optical spring - the sign flip is exact
    chk("spring_zero_on_resonance", spring_shift(g1, 0.0, KAPPA_RESOLVED) == 0.0)
    chk("spring_softens_on_red", spring_shift(g1, -OMEGA_M, KAPPA_RESOLVED) < 0.0)
    chk("spring_stiffens_on_blue", spring_shift(g1, OMEGA_M, KAPPA_RESOLVED) > 0.0)
    chk("spring_antisymmetric",
        abs(spring_shift(g1, -0.5 * OMEGA_M, KAPPA_RESOLVED)
            + spring_shift(g1, 0.5 * OMEGA_M, KAPPA_RESOLVED)) < 1e-6)
    chk("spring_sideband_magnitudes_equal",
        abs(abs(spring_shift(g1, -OMEGA_M, KAPPA_RESOLVED))
            - abs(spring_shift(g1, OMEGA_M, KAPPA_RESOLVED))) < 1e-6)

    # 5. blue-detuned fence - threshold where the policy says
    power_thr, coop_thr = blue_threshold()
    chk("blue_threshold_cooperativity_near_one", 0.9 < coop_thr < 1.1)
    chk("blue_gamma_total_crosses_zero",
        _gamma_total_at_power(power_thr / 4.0, OMEGA_M, KAPPA_RESOLVED) > 0.0
        and _gamma_total_at_power(power_thr * 4.0, OMEGA_M, KAPPA_RESOLVED) < 0.0)
    chk("blue_full_drive_unstable",
        _gamma_total_at_power(DRIVE_POWER, OMEGA_M, KAPPA_RESOLVED) < 0.0)

    # 6. regimes sweep - the floor grows with kappa, occupancy follows
    sweep = regimes_report()["cooling_sweep_red_sideband"]
    chk("sweep_floor_formula_all_rows",
        all(abs(r["floor_rates"] - r["floor_formula"]) / r["floor_formula"] < 0.02
            for r in sweep))
    chk("sweep_final_occupancy_rises_with_kappa",
        sweep[0]["n_final"] < sweep[-1]["n_final"])

    # 7. classifier - labels come from the lab's own policy
    rep = classifier_report()
    chk("classifier_resolved", rep["resolved_cooling"] == "resolved-sideband-cooling")
    chk("classifier_unresolved", rep["unresolved_sideband"] == "unresolved-sideband")
    chk("classifier_weak", rep["weak_drive"] == "weak-coupling")
    chk("classifier_strong", rep["strong_drive"] == "strong-coupling")
    chk("classifier_blue", rep["blue_detuned"] == "blue-detuned-unstable")
    chk("classifier_matches_policy_on_grid",
        all(classify_regime(ratio, coop, sign) == policy_label(ratio, coop, sign)
            for (ratio, coop, sign), _ in
            [((f[0], f[1], f[2]), lbl) for f, lbl in TRAINING_GRID]))
    chk("classifier_matches_policy_on_scenarios",
        all(classify_regime(*features) == policy_label(*features)
            for features in _scenario_features().values()))

    # gates + seats
    chk("hold_gates_14", len(HOLD_GATES) == 14
        and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_device_control_hold", gate("real_cavity_device_control") == "HOLD")
    chk("gate_gravitational_wave_hold", gate("gravitational_wave_detection_claim") == "HOLD")
    chk("gate_cooling_record_hold", gate("ground_state_cooling_record_claim") == "HOLD")
    chk("gate_sensing_hold", gate("quantum_sensing_deployment_claim") == "HOLD")
    chk("gate_sql_hold", gate("sql_beating_product_claim") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    brains = brains_report()
    chk("argon4_no_override", brains["decider"]["can_override_hold"] is False
        and brains["decider"]["seat"] == "Gemini Argon 4 Extended Thinking")
    chk("claude_no_override", brains["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", brains["flow"]["rendered"] is False
        and brains["flow"]["live"] == 0)
    return c


# ================================================================ CLI / demo
def demo():
    print("=" * 68)
    print("Optomechanics-Lab - linearized cavity optomechanics, graded")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    print("\n[1] THE HONEST CORE - what this lab does and does not claim")
    print("    One driven cavity, one mechanical oscillator, the linearized")
    print("    equations - with every parameter LABELLED as a teaching")
    print("    number. No device was built, cooled, or sensed; a computed")
    print("    occupancy is a property of the equations, not a record.")
    ledger = coupling_report()
    print("\n[2] Coupling ledger - one Lorentzian under everything")
    print(f"    g0/2pi = {ledger['g0_over_two_pi_hz']:.1f} Hz | "
          f"drive {ledger['drive_power_w'] * 1e6:.1f} uW | "
          f"flux {ledger['photon_flux_per_s']:.4e} photons/s")
    for row in ledger["rows"]:
        print(f"    {row['detuning']:16s} n_cav {row['n_cav']:12.1f} | "
              f"g/2pi {row['g_over_two_pi_hz']:10.1f} Hz | "
              f"g/kappa {row['g_over_kappa']:.4f} | C {row['cooperativity']:10.1f}")
    cool = cooling_report()
    print("\n[3] Sideband cooling - Delta = -omega_m, from n_th = 200")
    for name in ("resolved", "unresolved"):
        case = cool[name]
        print(f"    {name:10s} kappa/omega_m {case['kappa_over_omega_m']:.2f} | "
              f"Gamma_opt/2pi {case['gamma_opt_over_two_pi_hz']:9.1f} Hz")
        print(f"               floor: rates {case['backaction_floor_rates']:.6f} "
              f"vs formula (kappa/4w_m)^2 {case['backaction_floor_formula']:.6f} | "
              f"n_final {case['n_final_closed_form']:.6f}")
        curve = " -> ".join(f"{n:.4f}" for _, n in case["cooling_curve_us"])
        print(f"               n(t): {curve}")
    print("    -> the resolved device reaches the ground state (n < 1);")
    print("       the unresolved one's floor is above one phonon, so no")
    print("       drive power in this model ever gets it there.")
    omit = omit_report()
    print("\n[4] OMIT - a window burned into the cavity notch")
    print(f"    bare dip |t|^2 min {omit['bare_min_power']:.2e} | "
          f"window peak {omit['peak_power']:.6f} "
          f"(C/(1+C))^2 = {omit['peak_formula_c_over_1pc']:.6f}")
    print(f"    window FWHM {omit['window_fwhm_over_two_pi_hz']:.2f} Hz vs "
          f"gamma_m + Gamma_opt = "
          f"{omit['gamma_m_plus_gamma_opt_per_s'] / TWO_PI:.2f} Hz "
          f"(ratio {omit['fwhm_ratio_to_gamma_sum']:.3f}) | "
          f"notch FWHM {omit['cavity_notch_fwhm_per_s'] / TWO_PI:.1f} Hz")
    spring = spring_report()
    print("\n[5] Optical spring - the sign flips with the detuning")
    for row in spring["rows"]:
        print(f"    Delta/omega_m {row['delta_over_omega_m']:+.1f} | "
              f"shift/2pi {row['shift_over_two_pi_hz']:+10.1f} Hz | {row['sign']}")
    regimes = regimes_report()
    thr = regimes["blue_sideband_threshold"]
    print("\n[6] Blue-detuned fence - where the damping sign gives out")
    print(f"    Gamma_total = 0 at P = {thr['power_w'] * 1e9:.2f} nW, "
          f"C = {thr['cooperativity_at_threshold']:.3f} (threshold ~ 1)")
    print(f"    at the 1 uW headline drive Gamma_total = "
          f"{thr['gamma_total_at_drive_power_per_s']:.1f} /s < 0: unstable.")
    print("    -> a sign change in a rate equation is a fence, not a")
    print("       phonon-laser product. That claim is a HOLD gate.")
    print("\n[7] Regime classifier (TinyML kNN, labels from the lab policy)")
    for name, label in classifier_report().items():
        print(f"    {name:22s} -> {label}")
    print("\n[8] Advisory seats")
    brains = brains_report()
    print(f"    decider: {brains['decider']['decision']} "
          f"trace={brains['decider']['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {brains['advisor']['can_override_hold']}")
    print(f"    flow rendered = {brains['flow']['rendered']} "
          f"live = {brains['flow']['live']}")
    print(f"\n[9] HOLD gates: {len(HOLD_GATES)}")
    for key in HOLD_GATES:
        print(f"    HOLD  {key}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "coupling":
        print(json.dumps(coupling_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "cooling":
        print(json.dumps(cooling_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "omit":
        print(json.dumps(omit_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "spring":
        print(json.dumps(spring_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "regimes":
        print(json.dumps(regimes_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "classify":
        print(json.dumps(classifier_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for key, value in HOLD_GATES.items():
            print(f"{key}: {value}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "real_cavity_device_control"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
