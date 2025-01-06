from crewai.flow.flow import Flow, listen, start, router, and_
from pydantic import BaseModel
from litellm import completion


class ResearchFlowState(BaseModel):
    study_summary: str = ""
    recruitment_strategies: str = ""
    recruitment_document: str = ""
    score: int = 0
    feedback: str = ""


class ResearchFlow(Flow[ResearchFlowState]):
    model = "gpt-4o-mini"

    @start()
    def summarize_study(self):
        """
        Task 1: Summarize the study document.
        """
        print("Summarizing the study document...")
        response = completion(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": "Summarize the following study document: [INSERT STUDY DOCUMENT HERE].",
                }
            ],
        )
        self.state.study_summary = response["choices"][0]["message"]["content"]
        print(f"Study Summary: {self.state.study_summary}")
        return self.state.study_summary

    @listen(summarize_study)
    def search_recruitment_strategies(self):
        """
        Task 2: Search for recruitment strategies relevant to the study.
        """
        print("Searching for recruitment strategies...")
        response = completion(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"Search and summarize the best recruitment strategies for the following study: {self.state.study_summary}.",
                }
            ],
        )
        self.state.recruitment_strategies = response["choices"][0]["message"]["content"]
        print(f"Recruitment Strategies: {self.state.recruitment_strategies}")
        return self.state.recruitment_strategies

    @listen(search_recruitment_strategies)
    def generate_recruitment_document(self):
        """
        Task 3: Research writer produces a recruitment document.
        """
        print("Generating recruitment and retention document...")
        response = completion(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"Based on these recruitment strategies: {self.state.recruitment_strategies}, write a recruitment and retention document.",
                }
            ],
        )
        self.state.recruitment_document = response["choices"][0]["message"]["content"]
        print(f"Recruitment Document: {self.state.recruitment_document}")
        return self.state.recruitment_document

    @listen(generate_recruitment_document)
    def evaluate_document(self):
        """
        Task 4: Auditor evaluates the document and scores it out of 10.
        """
        print("Evaluating recruitment document...")
        response = completion(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"Evaluate the following recruitment document on a scale of 1 to 10 and provide feedback: {self.state.recruitment_document}",
                }
            ],
        )
        evaluation = response["choices"][0]["message"]["content"]
        score = int("".join(filter(str.isdigit, evaluation)))  # Extract the score
        self.state.score = score
        self.state.feedback = evaluation
        print(f"Score: {self.state.score}, Feedback: {self.state.feedback}")
        return self.state.score

    @router(evaluate_document)
    def routing_logic(self):
        """
        Route based on the score.
        """
        if self.state.score <= 7:
            return "update_document"
        else:
            return "end_flow"

    @listen("update_document")
    def update_document(self):
        """
        Loop back to update the document if score is ≤ 7.
        """
        print("Updating recruitment document based on feedback...")
        response = completion(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"Update the following document based on this feedback: {self.state.feedback}. Document: {self.state.recruitment_document}",
                }
            ],
        )
        self.state.recruitment_document = response["choices"][0]["message"]["content"]
        print(f"Updated Document: {self.state.recruitment_document}")
        return self.state.recruitment_document

    @listen("end_flow")
    def finalize_flow(self):
        """
        End the flow if the score is acceptable (>7).
        """
        print("Finalizing the flow. Recruitment document is approved.")
        return self.state.recruitment_document


# Instantiate and kickoff the flow
flow = ResearchFlow()


if __name__ == "__main__":
    # result = flow.kickoff()
    # print(result)
    flow.plot("Research Flow")
