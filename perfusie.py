# %%
from physiomodeler import Model

# %%
parameters = {
    "volume_PC": 0.1,
    "volume_SA": 1.1,
    "volume_SC": 0.3,
    "volume_SV": 3.5,
}

# %%
inputs = {
    "cardiac_output": 5 / 60,
    "flux_O2_SC_weefsels": 0.25 / 60,
    "flux_CO2_SC_weefsels": -0.2 / 60,
}


# %%
def dynamics(state, inputs, parameters):
    gas = parameters["gas"]
    compartiment_a = parameters["voorgaand_compartiment"]
    compartiment_b = parameters["compartiment"]

    inhoud_a = inputs[f"inhoud_{gas}_{compartiment_a}"]
    inhoud_b = state[f"inhoud_{gas}_{compartiment_b}"]
    volume_b = parameters[f"volume_{compartiment_b}"]
    cardiac_output = inputs["cardiac_output"]

    dinhoud_a_b = (
        (inhoud_a - inhoud_b) * cardiac_output / volume_b
    )
    if compartiment_b == "PC":
        dinhoud_flux = (
            inputs[f"flux_{gas}_alveoli_PC"] / volume_b
        )
    elif compartiment_b == "SC":
        dinhoud_flux = (
            -inputs[f"flux_{gas}_SC_weefsels"] / volume_b
        )
    else:
        dinhoud_flux = 0

    return {
        f"dinhoud_{gas}_{compartiment_b}": dinhoud_a_b
        + dinhoud_flux
    }


# %%
def dynamics(state, inputs, parameters):
    gas = parameters["gas"]
    compartiment_a = parameters["voorgaand_compartiment"]
    compartiment_b = parameters["compartiment"]

    inhoud_a = inputs[f"inhoud_{gas}_{compartiment_a}"]
    inhoud_b = state[f"inhoud_{gas}_{compartiment_b}"]
    volume_b = parameters[f"volume_{compartiment_b}"]
    cardiac_output = inputs["cardiac_output"]

    dinhoud_a_b = (
        (inhoud_a - inhoud_b) * cardiac_output / volume_b
    )
    if compartiment_b == "PC":
        dinhoud_flux = (
            inputs[f"flux_{gas}_alveoli_PC"] / volume_b
        )
    elif compartiment_b == "SC":
        dinhoud_flux = (
            -inputs[f"flux_{gas}_SC_weefsels"] / volume_b
        )
    else:
        dinhoud_flux = 0

    return {
        f"dinhoud_{gas}_{compartiment_b}": dinhoud_a_b
        + dinhoud_flux,
        f"delivery_{gas}_{compartiment_a}_{compartiment_b}": inhoud_a
        * cardiac_output,
    }


# %%
modellen = []
for gas in ("O2", "CO2"):
    for compartiment_a, compartiment_b in (
        ("SV", "PC"),
        ("PC", "SA"),
        ("SA", "SC"),
        ("SC", "SV"),
    ):
        model = Model(
            dynamics=dynamics,
            state_components=[
                f"inhoud_{gas}_{compartiment_b}"
            ],
            parameters={
                "gas": gas,
                "compartiment": compartiment_b,
                "voorgaand_compartiment": compartiment_a,
            },
        )
        modellen.append(model)


# %%
def event_concentratie_O2_negatief(state):
    return state["inhoud_O2_SC"]


event_concentratie_O2_negatief.terminal = True

# %%
perfusie_model = Model(
    dynamics=modellen,
    inputs=inputs,
    parameters=parameters,
    events=[event_concentratie_O2_negatief],
)
