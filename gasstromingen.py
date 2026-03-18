# %%
from physiomodeler import Model

# %%
inputs = {
    "fractie_O2_luchtwegopening": 0.1965,
    "fractie_CO2_luchtwegopening": 0.0003,
}


# %%
def fractie_verandering(
    fractie_a, fractie_b, debiet_a_b, volume_b
):
    if debiet_a_b <= 0:
        return 0

    return (fractie_a - fractie_b) * (debiet_a_b / volume_b)


# %%
def dynamics(state, inputs, parameters):
    gas = parameters["gas"]
    dfractie_LWO_LW = fractie_verandering(
        inputs[f"fractie_{gas}_luchtwegopening"],
        state[f"fractie_{gas}_luchtwegen"],
        inputs["debiet_luchtwegopening_luchtwegen"],
        inputs["volume_luchtwegen"],
    )
    dfractie_alv_LW = fractie_verandering(
        state[f"fractie_{gas}_alveoli"],
        state[f"fractie_{gas}_luchtwegen"],
        -inputs["debiet_luchtwegen_alveoli"],
        inputs["volume_luchtwegen"],
    )
    dfractie_LW_alv = fractie_verandering(
        state[f"fractie_{gas}_luchtwegen"],
        state[f"fractie_{gas}_alveoli"],
        inputs["debiet_luchtwegen_alveoli"],
        inputs["volume_alveoli"]/0.8,
    )
    dfractie_LW = dfractie_LWO_LW + dfractie_alv_LW
    dfractie_alv = (
        dfractie_LW_alv
        - inputs[f"flux_{gas}_alveoli_PC"]
        / inputs["volume_alveoli"]/0.8
    )

    return {
        f"dfractie_{gas}_luchtwegen": dfractie_LW,
        f"dfractie_{gas}_alveoli": dfractie_alv,
    }


# %%
gasstroming_O2_model = Model(
    dynamics=dynamics,
    state_components=[
        "fractie_O2_luchtwegen",
        "fractie_O2_alveoli",
    ],
    inputs=inputs,
    parameters={"gas": "O2"},
)

# %%
gasstroming_CO2_model = Model(
    dynamics=dynamics,
    state_components=[
        "fractie_CO2_luchtwegen",
        "fractie_CO2_alveoli",
    ],
    inputs=inputs,
    parameters={"gas": "CO2"},
)

# %%
gasstromingen_model = Model(
    dynamics=[gasstroming_O2_model, gasstroming_CO2_model],
)
