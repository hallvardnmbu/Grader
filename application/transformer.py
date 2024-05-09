from transformers import AutoTokenizer, AutoModelForCausalLM


def get_model(model, token=None):
    """
    Get the specified tokenizer and model.

    Parameters
    ----------
    model : str
        For example 'google/codegemma-7b-it', or path to local checkpoint.
    token : str, optional
        The authentication token to access the model (if required).

    Returns
    -------
    dict
    """
    tokenizer = AutoTokenizer.from_pretrained('meta-llama/Meta-Llama-3-8B' if model.startswith(".")
                                              else model,
                                              token=token)
    tokenizer.pad_token = tokenizer.eos_token
    return {
        "tokenizer": tokenizer,
        "model": AutoModelForCausalLM.from_pretrained(model, token=token),
    }


def evaluate(model, text, generate=50, **kwargs):
    """
    Get an output from the model.

    Parameters
    ----------
    model : dict
        Containing the tokenizer and model.
    text : str
        The prompt to send through the model.
    generate : int
        Maximum number of tokens to generate.
    kwargs : dict
        Other keyword-arguments sent to `transformers.AutoModelForCausalLM.generate()`.

    Returns
    -------
    str
        The output of the model.
    """
    data = model["tokenizer"](text, return_tensors="pt")

    attention_mask = data["input_ids"].ne(model["tokenizer"].pad_token_id).float()

    out = model["model"].generate(
        data["input_ids"], max_length=generate,
        num_beams=5, no_repeat_ngram_size=2,
        attention_mask=attention_mask,
        pad_token_id=model["tokenizer"].eos_token_id,
        **kwargs
    )
    return model["tokenizer"].decode(
        out[0, data["input_ids"].size(1):],
        skip_special_tokens=True, clean_up_tokenization_spaces=True
    )
