# Graph Architecture

```mermaid
flowchart TD
    START([START]) --> classify[classify<br/>LLM classification]

    classify -->|is_confident=true| retrieve_policy[retrieve_policy<br/>policy lookup]
    classify -->|is_confident=false| review_classification[[review_classification<br/>⏸ INTERRUPT]]

    review_classification --> retrieve_policy
    retrieve_policy --> decide[decide<br/>respond or escalate]

    decide -->|respond| draft[draft<br/>LLM reply]
    decide -->|escalate| review_escalation[[review_escalation<br/>⏸ INTERRUPT]]

    review_escalation -->|action=approve| END([END])
    review_escalation -->|action=respond| draft

    draft --> END