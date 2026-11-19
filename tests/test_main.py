"""Tests for Optomechanics-Lab: the coupling Lorentzian, scattering
rates vs the closed-form floors, the RK4 cooling curve, the OMIT
window read off the computed curve, the optical-spring sign flip,
the blue-detuned threshold, the kNN policy, HOLD gates, and
determinism."""
import math
import subprocess
import sys
from pathlib import Path

import main

ROOT = Path(__file__).resolve().parent.parent
RED = -main.OMEGA_M
BLUE = main.OMEGA_M
KAP = main.KAPPA_RESOLVED
N_RED = main.intracavity_photons(main.DRIVE_POWER, RED, KAP)
G_RED = main.enhanced_coupling(N_RED)


# ---------------------------------------------------------------- ledger
def test_photon_flux_value():
    flux = main.photon_flux(main.DRIVE_POWER)
    assert abs(flux - main.DRIVE_POWER / (main.HBAR * main.OMEGA_L)) < 1e-3 * flux


def test_n_cav_lorentzian_ordering():
    n0 = main.intracavity_photons(main.DRIVE_POWER, 0.0, KAP)
    n1 = main.intracavity_photons(main.DRIVE_POWER, RED, KAP)
    n2 = main.intracavity_photons(main.DRIVE_POWER, 2.0 * RED, KAP)
    assert n0 > n1 > n2 > 0.0


def test_enhanced_coupling_law():
    assert abs(G_RED - main.G0 * math.sqrt(N_RED)) < 1e-12 * G_RED


def test_cooperativity_definitions():
    c = main.cooperativity(G_RED, KAP)
    assert abs(c - 4.0 * G_RED ** 2 / (KAP * main.GAMMA_M)) < 1e-9
    assert abs(main.thermal_cooperativity(G_RED, KAP)
               - c / (2.0 * main.N_TH + 1.0)) < 1e-12


# ---------------------------------------------------------------- cooling
def test_a_minus_on_sideband():
    a_minus = main.rate_a_minus(G_RED, RED, KAP)
    assert abs(a_minus - 4.0 * G_RED ** 2 / KAP) < 1e-9 * a_minus


def test_gamma_opt_signs():
    assert main.gamma_opt(G_RED, RED, KAP) > 0.0
    assert main.gamma_opt(G_RED, BLUE, KAP) < 0.0


def test_resolved_floor_matches_formula():
    floor = main.backaction_floor(G_RED, RED, KAP)
    assert abs(floor - main.floor_formula(KAP)) / main.floor_formula(KAP) < 0.01


def test_resolved_ground_state_reached():
    n_fin = main.final_occupancy(G_RED, RED, KAP)
    assert 0.0 < n_fin < 1.0
    assert n_fin > main.backaction_floor(G_RED, RED, KAP)


def test_unresolved_floor_and_final_above_one():
    n_u = main.intracavity_photons(main.DRIVE_POWER, RED, main.KAPPA_UNRESOLVED)
    g_u = main.enhanced_coupling(n_u)
    assert main.backaction_floor(g_u, RED, main.KAPPA_UNRESOLVED) > 1.0
    assert main.final_occupancy(g_u, RED, main.KAPPA_UNRESOLVED) > 1.0


def test_cooling_curve_rk4_vs_exact_transient():
    curve = main.cooling_curve(G_RED, RED, KAP)
    assert curve[0][1] == main.N_TH
    assert all(curve[i][1] > curve[i + 1][1] for i in range(len(curve) - 1))
    n_fin = main.final_occupancy(G_RED, RED, KAP)
    exact = n_fin + (main.N_TH - n_fin) * math.exp(
        -main.gamma_total(G_RED, RED, KAP) * curve[-1][0])
    assert abs(curve[-1][1] - exact) / exact < 1e-4


# ---------------------------------------------------------------- OMIT
def test_omit_bare_dip_exactly_zero():
    assert main.omit_power(0.0, 0.0, KAP) < 1e-24


def test_omit_peak_formula():
    report = main.omit_report()
    assert abs(report["peak_power"] - report["peak_formula_c_over_1pc"]) < 1e-9
    assert report["peak_power"] > 0.99


def test_omit_fwhm_against_gamma_sum():
    report = main.omit_report()
    assert 0.70 < report["fwhm_ratio_to_gamma_sum"] < 1.30
    assert report["window_fwhm_per_s"] < report["cavity_notch_fwhm_per_s"]


# ---------------------------------------------------------------- spring
def test_spring_sign_flip_at_sidebands():
    assert main.spring_shift(G_RED, RED, KAP) < 0.0
    assert main.spring_shift(G_RED, BLUE, KAP) > 0.0
    assert main.spring_shift(G_RED, 0.0, KAP) == 0.0


def test_spring_antisymmetry():
    for frac in (0.5, 1.0, 2.0):
        plus = main.spring_shift(G_RED, frac * main.OMEGA_M, KAP)
        minus = main.spring_shift(G_RED, -frac * main.OMEGA_M, KAP)
        assert abs(plus + minus) < 1e-6


# ---------------------------------------------------------------- blue fence
def test_blue_threshold_cooperativity_near_one():
    _, coop = main.blue_threshold()
    assert 0.9 < coop < 1.1


def test_blue_gamma_total_crosses_zero():
    power, _ = main.blue_threshold()
    assert main._gamma_total_at_power(power / 4.0, BLUE, KAP) > 0.0
    assert main._gamma_total_at_power(power * 4.0, BLUE, KAP) < 0.0
    assert main._gamma_total_at_power(main.DRIVE_POWER, BLUE, KAP) < 0.0


# ---------------------------------------------------------------- regimes
def test_sweep_floors_match_formula():
    for row in main.regimes_report()["cooling_sweep_red_sideband"]:
        assert abs(row["floor_rates"] - row["floor_formula"]) / row["floor_formula"] < 0.02


# ---------------------------------------------------------------- classifier
def test_classifier_scenarios():
    rep = main.classifier_report()
    assert rep["resolved_cooling"] == "resolved-sideband-cooling"
    assert rep["unresolved_sideband"] == "unresolved-sideband"
    assert rep["weak_drive"] == "weak-coupling"
    assert rep["strong_drive"] == "strong-coupling"
    assert rep["blue_detuned"] == "blue-detuned-unstable"


def test_classifier_matches_policy_everywhere():
    for features in main._scenario_features().values():
        assert main.classify_regime(*features) == main.policy_label(*features)
    for features, label in main.TRAINING_GRID:
        assert main.classify_regime(features[0], features[1], features[2]) == label


# ---------------------------------------------------------------- gates + seats
def test_hold_gates():
    assert len(main.HOLD_GATES) == 14
    assert main.gate("real_cavity_device_control") == "HOLD"
    assert main.gate("gravitational_wave_detection_claim") == "HOLD"
    assert main.gate("ground_state_cooling_record_claim") == "HOLD"
    assert main.gate("run_simulation") == "PROCEED"


def test_seats_never_override():
    brains = main.brains_report()
    assert brains["decider"]["seat"] == "Gemini Argon 4 Extended Thinking"
    assert brains["decider"]["can_override_hold"] is False
    assert brains["advisor"]["can_override_hold"] is False
    assert brains["flow"]["rendered"] is False and brains["flow"]["live"] == 0


def test_checks_all_pass():
    checks = main.run_checks()
    assert all(ok for _, ok in checks), [n for n, ok in checks if not ok]


# ---------------------------------------------------------------- CLI
def _run(*args):
    return subprocess.run([sys.executable, "main.py", *args],
                          cwd=ROOT, capture_output=True, text=True)


def test_cli_demo_exit_zero():
    assert _run("demo").returncode == 0


def test_cli_demo_byte_identical():
    assert _run("demo").stdout == _run("demo").stdout


def test_cli_checks_line():
    out = _run("checks").stdout
    total = len(main.run_checks())
    assert f"CHECKS {total}/{total}" in out


def test_cli_hold_demo_exit_2():
    assert _run("hold-demo").returncode == 2


def test_cli_topic_commands():
    for cmd in ("coupling", "cooling", "omit", "spring", "regimes",
                "classify", "brains", "holds"):
        assert _run(cmd).returncode == 0, cmd
