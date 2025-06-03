# AnnaAgent

The code for the paper `AnnaAgent: Dynamic Evolution Agent System with Multi-Session Memory for Realistic Seeker Simulation`.

## CLAIM

It is important to note that since this work involves data from counselling records of **real patients** with psychological disorders, the publicly available code can only be used to demonstrate part of the methodology. Please contact the authors of [this paper](https://aclanthology.org/2022.emnlp-main.156/) if needed.

## How to Run the Example
First, you need to deploy the servers with these commands:

```bash
# need vllm, the version we used is 0.6.4.
bash complaint.sh
bash counselor.sh
bash emotion.sh
```

The trained model will be updated here at the end of the submission progress. You can also use an untrained LLM as an alternative, it might be less effective.

There is a inner example in the `run.py`. You can easily run it just with the following command:

```bash
python run.py
```

Then, you can chat with the virtual seeker.

## Work Progress

To make it easier for readers to learn how to use it, we add the flowchart below:

![](https://github.com/sci-m-wang/AnnaAgent/blob/main/figure/whiteboard_exported_image_en.png)

With two groups of agents (for **Dynamic Evolution** & **Multi-session Memory**, respectively), AnnaAgent simulates seekers via two main stages, i.e., the **initialization stage** to set the seeker's configuration (including profile, situation, symptoms, etc) and the **conversation stage** to interact with the counselor. The agent group for dynamic evolution contains an emotion modulator, a chief complaint chain generator and a complaint switcher. There are three agents in the agent group for multi-session memory: a situation analyzer, a status analyzer, and a memory retriever.

In addition, there are supplementary modules for speaking style analysis, scale summarization and event selection.

At the initialization stage, the seeker's **basic profile** and historical session conversations and reports from **long-term memory** are first read. The seeker's style is analyzed based on previous session's conversations by the *speaking style analysis module* next. The *scale summarization module* summarizes **historical scales** based on the seeker's profile and reports. Then, the *event selection module* matches a suitable event based on the seeker's profile and the *situation analyzer* generates a situation that the seeker encounters based on the event. Meanwhile, the virtual seeker is required to complete the scales for the **current session** based on the current configurations and the *status analyzer* analyzes the change in the seeker's status based on the two groups of scales. Situations and statuses together make up **short-term memory**. In addition, the **chief complaint chain generator** generates a chief complaint chain based on the seeker's profile and long-term memory during the initialization stage.

At the **conversation stage**, AnnaAgent has a conversation with a counselor. For each utterance by the counselor, the *memory retriever* determines whether long-term memory needs to be **retrieved**. If it is needed, relevant information is retrieved from conversations and reports from **previous sessions**. In addition, the *emotion modulator* reasons the **seeker's next emotion** and performs emotion perturbation on a probability basis according to the real-time memory, i.e., the context of the conversation. After the seeker completes an utterance, the *complaint switcher* decides whether or not to awaken the seeker's **next chief complaint stage**.

## Citation
```bibtex
@article{wang2025annaagentdynamicevolutionagent,
      title={AnnaAgent: Dynamic Evolution Agent System with Multi-Session Memory for Realistic Seeker Simulation}, 
      author={Ming Wang and Peidong Wang and Lin Wu and Xiaocui Yang and Daling Wang and Shi Feng and Yuxin Chen and Bixuan Wang and Yifei Zhang},
      year={2025},
      eprint={2506.00551},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2506.00551}, 
}
```
