# %% [markdown]
# ## Deel 5 - Functionele verdeling

# %%
from physiomodeler import Model
import scipy as sp
import numpy as np

# %%
parameters_luchtstromingen = {
    "weerstand_luchtwegopening_luchtwegen": 3.0,
    "weerstand_luchtwegen_alveoli": 2.0,
}
parameters_dynamische_elastantie = {
    "g_thoraxwand": (5, 4.6, -240, -2.3, 0),
    "g_luchtwegen": [11, 0.2, 1e-3, 8, -0.06],
    "g_alveoli": [2.75, 0.8, 1e-3, 2, -0.24],
}


# %%
def input_druk_als_blokgolf(time, inputs):
    periode = 60 / inputs["ademhalingsfrequentie"]
    blokgolf = sp.signal.square(
        time * 2 * np.pi / periode, duty=inputs["druk_duty"]
    )
    luchtwegdruk = (
        (blokgolf + 1)
        / 2
        * inputs["amplitude_luchtwegdruk"]
    )
    luchtwegdruk += inputs["PEEP"]
    return luchtwegdruk


# %%
inputs = {
    "druk_luchtwegopening": input_druk_als_blokgolf,
    "amplitude_luchtwegdruk": 5,
    "ademhalingsfrequentie": 12,
    "druk_duty": 0.4,
    "PEEP": 0.0,
}


# %%
def elastische_druk(volume, g):
    return (
        g[0] * (volume - g[1])
        + g[2] * np.exp(g[3] * volume)
        + g[4] / volume
    )


# %%
def drukken_dynamische_elastantie(inputs, parameters):
    V_luchtwegen = inputs["volume_luchtwegen"]
    V_alveoli = inputs["volume_alveoli"]
    V_longen = V_luchtwegen + V_alveoli

    P_E_luchtwegen = elastische_druk(
        V_luchtwegen, parameters["g_luchtwegen"]
    )
    P_E_alveoli = elastische_druk(
        V_alveoli, parameters["g_alveoli"]
    )
    P_E_thoraxwand = elastische_druk(
        V_longen, parameters["g_thoraxwand"]
    )

    return {
        "druk_pleura": P_E_thoraxwand,
        "transpulmonale_druk": P_E_alveoli,
        "druk_alveoli": P_E_alveoli + P_E_thoraxwand,
        "elastische_druk_luchtwegen": P_E_luchtwegen,
        "druk_luchtwegen": P_E_luchtwegen + P_E_thoraxwand,
        "volume_longen": V_longen,
    }


dynamische_elastantie_drukken_model = Model(
    dynamics=drukken_dynamische_elastantie,
    parameters=parameters_dynamische_elastantie,
)


# %%
def dynamics(inputs, parameters):
    """Dynamica van een simpel ballon-model van de longen."""
    R_LWO_LW = parameters[
        "weerstand_luchtwegopening_luchtwegen"
    ]
    R_LW_alv = parameters["weerstand_luchtwegen_alveoli"]
    P_LWO = inputs["druk_luchtwegopening"]
    P_LW = inputs["druk_luchtwegen"]
    P_alv = inputs["druk_alveoli"]

    Q_LWO_LW = (P_LWO - P_LW) / R_LWO_LW
    Q_LW_alv = (P_LW - P_alv) / R_LW_alv

    dV_LW = Q_LWO_LW - Q_LW_alv

    totale_flux = (
        inputs["flux_O2_alveoli_PC"]
        + inputs["flux_CO2_alveoli_PC"]
    )
    dV_alv = Q_LW_alv - totale_flux

    return {
        "dvolume_luchtwegen": dV_LW,
        "dvolume_alveoli": dV_alv,
        "debiet_luchtwegopening_luchtwegen": Q_LWO_LW,
        "debiet_luchtwegen_alveoli": Q_LW_alv,
    }


# %%
luchtstromingen_model = Model(
    dynamics=[
        dynamische_elastantie_drukken_model,
        dynamics,
    ],
    state_components=[
        "volume_luchtwegen",
        "volume_alveoli",
    ],
    inputs=inputs,
    parameters=parameters_luchtstromingen,
)

# %%
luchtstromingen_model_init = luchtstromingen_model.replace(
    initial_state={
        "volume_luchtwegen": 0.7,
        "volume_alveoli": 2.8,
    },
)
