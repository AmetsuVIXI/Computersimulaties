# %%
import numpy as np
from physiomodeler import Model

# %%dddd
inputs = {
    "druk_atmosfeer": 1033,  # cmH2O
}

# %%
parameters = {
    "kPa_per_cmH2O": 0.0981,  # kPa/cmH2O,
    "bindingscapaciteit_Hb_per_gram": 1.35e-3,  # L(O2)/g(Hb)
    "concentratie_Hb": 150,  # g(Hb)/L(bloed)
    "diffusiecapaciteit_O2_alveoli_PC": 0.0042,  # L/(s*kPa)
    "diffusiecapaciteit_CO2_alveoli_PC": 0.025,
}


# %%
def partiele_drukken_lucht(inputs):
    P_alv_abs_cmH2O = (
        inputs["druk_alveoli"] + inputs["druk_atmosfeer"]
    )
    P_alv_abs_kPa = (
        P_alv_abs_cmH2O * parameters["kPa_per_cmH2O"]
    )
    return {
        "partiele_druk_O2_alveoli": P_alv_abs_kPa
        * inputs["fractie_O2_alveoli"],
        "partiele_druk_CO2_alveoli": P_alv_abs_kPa
        * inputs["fractie_CO2_alveoli"],
    }


# %%
def partiele_drukken_lucht(inputs):
    resultaten = {}
    for compartiment in ["alveoli", "luchtwegen"]:
        P_abs_cmH2O = (
            inputs[f"druk_{compartiment}"]
            + inputs["druk_atmosfeer"]
        )
        P_abs_kPa = (
            P_abs_cmH2O * parameters["kPa_per_cmH2O"]
        )
        resultaten.update(
            {
                f"partiele_druk_O2_{compartiment}": P_abs_kPa
                * inputs[f"fractie_O2_{compartiment}"],
                f"partiele_druk_CO2_{compartiment}": P_abs_kPa
                * inputs[f"fractie_CO2_{compartiment}"],
            }
        )
    return resultaten


# %%
def partiele_druk_O2_bij_saturatie(saturatie):
    h2 = 2.81
    y_N = 55.5 * saturatie / (1 - saturatie)

    a = (y_N + np.sqrt(y_N**2 + h2)) / 2
    b = (y_N - np.sqrt(y_N**2 + h2)) / 2

    # Een negatief getal tot een breuk verheffen geeft een complex getal. In
    # plaats daarvan converteren we naar een positief getal en zetten we het
    # originele teken er weer bij terug na machtsverheffing.
    # np.abs(a) converteert a naar een positief getal.
    # np.sign(a) converteert na machtsverheffing terug naar het originele teken.
    return np.sign(a) * np.abs(a) ** (1 / 3) + np.sign(
        b
    ) * np.abs(b) ** (1 / 3)


# %%
def partiele_druk_CO2_bij_inhoud(inhoud):
    return 0.837 * np.exp(4.16 * inhoud) - 0.895


# %%
def partiele_drukken_bloed(inputs, parameters):
    concentratie_Hb = parameters["concentratie_Hb"]
    bindingscapaciteit_O2_Hb = parameters[
        "bindingscapaciteit_Hb_per_gram"
    ]

    totale_bindingscapaciteit_O2 = (
        concentratie_Hb * bindingscapaciteit_O2_Hb
    )
    saturatie_O2 = (
        inputs["inhoud_O2_PC"]
        / totale_bindingscapaciteit_O2
    )

    return {
        "partiele_druk_O2_PC": partiele_druk_O2_bij_saturatie(
            saturatie_O2
        ),
        "saturatie_O2_PC": saturatie_O2,
        "partiele_druk_CO2_PC": partiele_druk_CO2_bij_inhoud(
            inputs["inhoud_CO2_PC"]
        ),
    }


# %%
def partiele_drukken_bloed(inputs, parameters):
    concentratie_Hb = parameters["concentratie_Hb"]
    bindingscapaciteit_O2_Hb = parameters[
        "bindingscapaciteit_Hb_per_gram"
    ]
    totale_bindingscapaciteit_O2 = (
        concentratie_Hb * bindingscapaciteit_O2_Hb
    )

    resultaten = {}
    for compartiment in ["PC", "SA", "SC", "SV"]:
        resultaten[f"saturatie_O2_{compartiment}"] = (
            inputs[f"inhoud_O2_{compartiment}"]
            / totale_bindingscapaciteit_O2
        )

        resultaten[f"partiele_druk_O2_{compartiment}"] = (
            partiele_druk_O2_bij_saturatie(
                resultaten[f"saturatie_O2_{compartiment}"]
            )
        )
        resultaten[f"partiele_druk_CO2_{compartiment}"] = (
            partiele_druk_CO2_bij_inhoud(
                inputs[f"inhoud_CO2_{compartiment}"]
            )
        )

    return resultaten


# %%
def flux_alveoli_PC(parameters, inputs):
    gas = parameters["gas"]

    diffusiecapaciteit = parameters[
        f"diffusiecapaciteit_{gas}_alveoli_PC"
    ]

    partiele_druk_alveoli = inputs[
        f"partiele_druk_{gas}_alveoli"
    ]
    partiele_druk_PC = inputs[f"partiele_druk_{gas}_PC"]

    return {
        f"flux_{gas}_alveoli_PC": diffusiecapaciteit
        * (partiele_druk_alveoli - partiele_druk_PC)
    }


# %%
flux_O2_alveoli_PC_model = Model(
    dynamics=flux_alveoli_PC,
    parameters={"gas": "O2"},
)

flux_CO2_alveoli_PC_model = Model(
    dynamics=flux_alveoli_PC,
    parameters={"gas": "CO2"},
)

# %%
flux_alveoli_PC_model = Model(
    dynamics=[
        partiele_drukken_lucht,
        partiele_drukken_bloed,
        flux_O2_alveoli_PC_model,
        flux_CO2_alveoli_PC_model,
    ],
    parameters=parameters,
    inputs=inputs,
)
