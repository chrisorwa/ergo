import jax.numpy as np
import numpy as onp
import pytest
import scipy.stats

from ergo import Logistic, LogisticMixture, TruncatedLogisticMixture
from ergo.scale import Scale


def test_cdf():
    xscale = Scale(-50, 150)
    scipydist_normed = scipy.stats.logistic(0.5, 0.05)
    scipydist_true = scipy.stats.logistic(50, 10)
    ergodist = Logistic(loc=50, s=10, scale=xscale)

    for x in np.linspace(0, 1, 10):
        assert scipydist_normed.cdf(x) == pytest.approx(
            float(ergodist.cdf(xscale.denormalize_point(x))), rel=1e-3
        )

    for x in np.linspace(-50, 150, 10):
        assert scipydist_true.cdf(x) == pytest.approx(float(ergodist.cdf(x)), rel=1e-3)


# TODO test truncated Logistic better in this file


@pytest.mark.slow
def test_pdf(logistic_mixture_p_uneven):
    ## on normed scale ##
    xscale = Scale(0, 1)
    ergoLogisticMixture = LogisticMixture(
        components=[
            Logistic(loc=0.2, s=0.5, scale=xscale),
            Logistic(loc=0.8, s=0.1, scale=xscale),
        ],
        probs=[1.8629593e-29, 1.0],
        scale=xscale,
    )
    ergoLogistic = Logistic(loc=0.8, s=0.1, scale=xscale)
    scipydist = scipy.stats.logistic(0.8, 0.1)
    for x in np.linspace(0, 1, 10):
        assert (
            scipydist.pdf(x)
            == pytest.approx(float(ergoLogistic.pdf(x)), rel=1e-3)
            == pytest.approx(float(ergoLogisticMixture.pdf(x)), rel=1e-3)
        )

    ## linear scale ##
    xscale = Scale(0, 100)
    ergoLogisticMixture = LogisticMixture(
        components=[
            Logistic(loc=20, s=50, scale=xscale),
            Logistic(loc=80, s=10, scale=xscale),
        ],
        probs=[1.8629593e-29, 1.0],
        scale=xscale,
    )
    ergoLogistic = Logistic(loc=80, s=10, scale=xscale)
    scipydist = scipy.stats.logistic(80, 10)
    for x in np.linspace(0, 100, 10):
        assert (
            scipydist.pdf(x)
            == pytest.approx(float(ergoLogistic.pdf(x)), rel=1e-3)
            == pytest.approx(float(ergoLogisticMixture.pdf(x)), rel=1e-3)
        )

    ## more chaotic linear scale ##
    xscale = Scale(0, 58)
    ergoLogisticMixture = LogisticMixture(
        components=[
            Logistic(loc=20, s=50, scale=xscale),
            Logistic(loc=15, s=5, scale=xscale),
        ],
        probs=[1.8629593e-29, 1.0],
        scale=xscale,
    )
    ergoLogistic = Logistic(loc=15, s=5, scale=xscale)
    scipydist = scipy.stats.logistic(15, 5)
    for x in np.linspace(0, 58, 14):
        assert (
            scipydist.pdf(x)
            == pytest.approx(float(ergoLogistic.pdf(x)), rel=1e-3)
            == pytest.approx(float(ergoLogisticMixture.pdf(x)), rel=1e-3)
        )


@pytest.mark.parametrize(
    "LogisticMixtureClass", [LogisticMixture, TruncatedLogisticMixture]
)
def test_fit_mixture_small(LogisticMixtureClass):
    xscale = Scale(-2, 3)
    mixture = LogisticMixtureClass.from_samples(
        data=np.array([0.1, 0.2, 0.8, 0.9]),
        fixed_params={"num_components": 2, "floor": -2, "ceiling": 3},
        scale=xscale,
    )
    for prob in mixture.probs:
        assert prob == pytest.approx(0.5, 0.1)
    locs = sorted([component.loc for component in mixture.components])
    assert locs[0] == pytest.approx(xscale.normalize_point(0.15), abs=0.1)
    assert locs[1] == pytest.approx(xscale.normalize_point(0.85), abs=0.1)


@pytest.mark.parametrize(
    "LogisticMixtureClass", [LogisticMixture, TruncatedLogisticMixture]
)
def test_fit_mixture_large(LogisticMixtureClass):
    xscale = Scale(-2, 3)
    data1 = onp.random.logistic(loc=0.7, scale=0.1, size=1000)
    data2 = onp.random.logistic(loc=0.4, scale=0.2, size=1000)
    data = onp.concatenate([data1, data2])
    mixture = LogisticMixtureClass.from_samples(
        data=data,
        fixed_params={"num_components": 2, "floor": -2, "ceiling": 3},
        scale=xscale,
    )
    components = sorted(
        [
            (component.loc, component.true_s, component.scale)
            for component in mixture.components
        ]
    )
    assert components[0][0] == pytest.approx(xscale.normalize_point(0.4), abs=0.2)
    assert components[1][0] == pytest.approx(xscale.normalize_point(0.7), abs=0.2)
    assert components[0][1] == pytest.approx(0.2, abs=0.2)
    assert components[1][1] == pytest.approx(0.1, abs=0.2)


def test_mixture_cdf(logistic_mixture15):
    # Use a mixture with known properties. The median should be 15 for this mixture.
    cdf50 = logistic_mixture15.cdf(15)
    assert cdf50 == pytest.approx(0.5, rel=1e-3)


def test_mixture_ppf(logistic_mixture10):
    # Use a mixtures with known properties. The median should be 10 for this mixture.
    ppf5 = logistic_mixture10.ppf(0.5)
    assert ppf5 == pytest.approx(10, rel=1e-3)


def test_mixture_ppf_adversarial(
    logistic_mixture_p_uneven, logistic_mixture_p_overlapping
):
    # Use a mixture with one very improbable distribution and one dominant distribution
    # Use a mixture with two hugely overlapping distributions

    assert logistic_mixture_p_uneven.ppf(0.5) == pytest.approx(5.0, rel=1e-3)
    assert logistic_mixture_p_uneven.ppf(0.01) == pytest.approx(-17.9755, rel=1e-3)
    assert logistic_mixture_p_uneven.ppf(0.001) == pytest.approx(-29.5337, rel=1e-3)
    assert logistic_mixture_p_uneven.ppf(0.99) == pytest.approx(27.9755, rel=1e-3)
    assert logistic_mixture_p_uneven.ppf(0.999) == pytest.approx(39.5337, rel=1e-3)

    assert logistic_mixture_p_overlapping.ppf(0.5) == pytest.approx(
        4000000.0342351394, rel=1e-3
    )
    assert logistic_mixture_p_overlapping.ppf(0.01) == pytest.approx(
        3080976.018257023, rel=1e-3
    )
    assert logistic_mixture_p_overlapping.ppf(0.001) == pytest.approx(
        2618649.009437881, rel=1e-3
    )
    assert logistic_mixture_p_overlapping.ppf(0.99) == pytest.approx(
        4919024.050213255, rel=1e-3
    )
    assert logistic_mixture_p_overlapping.ppf(0.999) == pytest.approx(
        5381351.059032397, rel=1e-3
    )


def test_ppf_cdf_round_trip():
    mixture = LogisticMixture.from_samples(
        np.array([0.5, 0.4, 0.8, 0.8, 0.9, 0.95, 0.15, 0.1]), {"num_components": 3}
    )
    x = 0.65
    prob = mixture.cdf(x)
    assert mixture.ppf(prob) == pytest.approx(x, rel=1e-3)


@pytest.mark.xfail(reason="Fitting to samples doesn't reliably work yet #219")
def test_fit_samples(logistic_mixture):
    data = np.array([logistic_mixture.sample() for _ in range(0, 1000)])
    fitted_mixture = LogisticMixture.from_samples(data, {"num_components": 2})
    true_locs = sorted([c.loc for c in logistic_mixture.components])
    true_scales = sorted([c.s for c in logistic_mixture.components])
    fitted_locs = sorted([c.loc for c in fitted_mixture.components])
    fitted_scales = sorted([c.s for c in fitted_mixture.components])
    for (true_loc, fitted_loc) in zip(true_locs, fitted_locs):
        assert fitted_loc == pytest.approx(float(true_loc), rel=0.2)
    for (true_scale, fitted_scale) in zip(true_scales, fitted_scales):
        assert fitted_scale == pytest.approx(float(true_scale), rel=0.2)


def test_logistic_mixture_normalization():
    scale = Scale(-50, 50)
    scalex2 = Scale(-100, 100)
    mixture = LogisticMixture(
        components=[Logistic(-40, 1, scale), Logistic(50, 10, scale)],
        probs=[0.5, 0.5],
        scale=scale,
    )

    mixturex2 = LogisticMixture(
        components=[Logistic(-80, 2, scalex2), Logistic(100, 20, scalex2)],
        probs=[0.5, 0.5],
        scale=scalex2,
    )

    assert mixturex2 == mixture.normalize().denormalize(scalex2)
    assert mixture == mixturex2.normalize().denormalize(scale)

    normalized = (
        mixture.normalize()
    )  # not necessary to normalize but here for readability

    assert normalized == LogisticMixture(
        [Logistic(0.1, 0.01, Scale(0, 1)), Logistic(1, 0.1, Scale(0, 1))],
        [0.5, 0.5],
        Scale(0, 1),
    )
