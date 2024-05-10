def generate_prompt(product, description):
    prompt = \
        f"""Here is a description for the product {{{product}}} inside <description></description> XML tags.
<description>{description}</description>

Please write a new comprehensive description in persian for the product using following three steps:
1. Write an introduction about product in a <p></p> html tag.
1. Extract all features and capabilities of the product from the description.
2. Put each feature or capability in a <h2></h2> html tag and expand it comprehensively in a <p></p> html tag.

Put your description in <response></response> XML tags."""
    return prompt