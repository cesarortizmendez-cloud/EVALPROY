from django import forms


def _parsear_lista_numeros(texto, nombre_campo):
    texto = texto.strip()
    if not texto:
        raise forms.ValidationError(f"Debes ingresar al menos un valor en '{nombre_campo}'.")
    partes = [p.strip() for p in texto.replace("\n", ",").split(",") if p.strip() != ""]
    valores = []
    for p in partes:
        try:
            valores.append(float(p))
        except ValueError:
            raise forms.ValidationError(f"'{p}' no es un número válido en '{nombre_campo}'.")
    return valores


class SensibilidadForm(forms.Form):
    flujos_base = forms.CharField(
        label="Flujo de caja base (año 0, año 1, …)",
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control", "placeholder": "-1000000, 400000, 450000, 500000"}),
        help_text="El primer valor (inversión) se mantiene fijo; los flujos futuros (años 1 en adelante) son los que se sensibilizan.",
    )
    tasa_descuento = forms.FloatField(
        label="Tasa de descuento (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )

    def clean_flujos_base(self):
        return _parsear_lista_numeros(self.cleaned_data["flujos_base"], "Flujo de caja base")

    def clean_tasa_descuento(self):
        return self.cleaned_data["tasa_descuento"] / 100


class EscenarioIndividualForm(forms.Form):
    nombre = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control form-control-sm"}))
    probabilidad = forms.FloatField(widget=forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01"}))
    flujos = forms.CharField(widget=forms.Textarea(attrs={"rows": 2, "class": "form-control form-control-sm"}))

    def clean_flujos(self):
        return _parsear_lista_numeros(self.cleaned_data["flujos"], "Flujos del escenario")


from django.forms import formset_factory

EscenarioFormSet = formset_factory(EscenarioIndividualForm, extra=3, min_num=2, validate_min=True)


class EscenariosTasaForm(forms.Form):
    tasa_descuento = forms.FloatField(
        label="Tasa de descuento (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )

    def clean_tasa_descuento(self):
        return self.cleaned_data["tasa_descuento"] / 100


class ArbolDecisionForm(forms.Form):
    """
    Árbol de decisión simplificado de 2 niveles, el caso clásico de curso:
    Decisión inicial (ej. Invertir / No invertir) -> si se invierte, nodo de
    azar con 2 escenarios (éxito/fracaso) cada uno con su probabilidad y flujo.
    """
    costo_invertir = forms.FloatField(
        label="Costo de invertir (inversión inicial, $)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    prob_exito = forms.FloatField(
        label="Probabilidad de éxito (0 a 1)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        help_text="La probabilidad de fracaso se calcula automáticamente como (1 - probabilidad de éxito).",
    )
    flujo_exito = forms.FloatField(
        label="Flujo si hay éxito ($)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    flujo_fracaso = forms.FloatField(
        label="Flujo si hay fracaso ($)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    flujo_no_invertir = forms.FloatField(
        label="Flujo de no invertir (normalmente 0, $)",
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class OpcionRealForm(forms.Form):
    valor_activo = forms.FloatField(
        label="Valor presente del proyecto si se invierte hoy, S ($)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Valor presente de los flujos futuros que generaría el proyecto si decides invertir ahora mismo.",
    )
    precio_ejercicio = forms.FloatField(
        label="Inversión requerida, K ($)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Monto que deberías desembolsar para ejecutar el proyecto (equivalente al 'precio de ejercicio' de la opción).",
    )
    tasa_libre_riesgo = forms.FloatField(
        label="Tasa libre de riesgo (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    volatilidad = forms.FloatField(
        label="Volatilidad anual del valor del proyecto (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej: 30"}),
        help_text="Qué tan inciertos son los flujos futuros del proyecto. A mayor incertidumbre, más valiosa es la opción de esperar.",
    )
    tiempo_anos = forms.FloatField(
        label="Tiempo durante el cual existe la opción (años)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
        help_text="Por ejemplo, plazo de una concesión, patente o derecho de exploración antes de que la oportunidad desaparezca.",
    )

    def clean_tasa_libre_riesgo(self):
        return self.cleaned_data["tasa_libre_riesgo"] / 100

    def clean_volatilidad(self):
        return self.cleaned_data["volatilidad"] / 100
