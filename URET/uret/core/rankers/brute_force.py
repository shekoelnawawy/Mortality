from uret.core.rankers.ranking_algorithm import RankingAlgorithm
import warnings
import copy
# Nawawy's MIMIC start
import numpy as np
import torch
# Nawawy's MIMIC end
class BruteForce(RankingAlgorithm):
    """
    This implementation tries all transformations and parameters for each given sample,
    and returns the list of them with scores and applied transformations.
    """

    def __init__(self, transformer_list, multi_feature_input=False, is_trained=True):
        """
        :param transformer_list: List of available transformations to be used by the algorithm.
        :param multi_feature_input: A boolean flag indicating if each index in the transformer
            list defines a transformer(s) for a single data type in the input. If False, then it
            is assumed that the transformer list defines multiple transformers for a single input
        :param is_trained: Indicates when _train has been called at least once. Always True
        """
        super().__init__(transformer_list, multi_feature_input, is_trained=True)

    # Nawawy's start
    def rank_edges(self, sample, scoring_function, score_input, model_predict, feature_extractor, dependencies=[],
                   current_transformation_records=None):
        backcast = sample[1]
        nv = sample[2]
        # Nawawy's MIMIC start
        original_sample = sample[0]
        sample = sample[0][1]
        number_of_instances = len(sample)
        sample = np.array(sample).reshape(number_of_instances*backcast*nv)
        # Nawawy's MIMIC end
    # Nawawy's end

        # Create transformation record
        if self.multi_feature_input and current_transformation_records is None:
            current_transformation_records = [None for _ in range(len(self.transformer_list))]

        return_values = []  # This will contain the (sample_index, transformer, action args, transformed sample,
        # transformation_record of the transformed sample, score)

        for transformer_index, (transformer, input_index) in enumerate(self.transformer_list):
            if self.multi_feature_input:
                possible_actions = transformer.get_possible(
                    sample[input_index], transformation_record=current_transformation_records[transformer_index]
                )
            else:
                possible_actions = transformer.get_possible(
                    sample, transformation_record=current_transformation_records
                )
            for action in possible_actions:
                sample_temp = copy.copy(sample)
                transformation_records_temp = copy.deepcopy(current_transformation_records)

                if self.multi_feature_input:
                    transformed_value, new_transformation_record = transformer.transform(
                        sample_temp[input_index],
                        transformation_record=transformation_records_temp[transformer_index],
                        transformation_value=action,
                    )
                    sample_temp[input_index] = transformed_value
                    transformation_records_temp[transformer_index] = new_transformation_record
                else:
                    transformed_value, new_transformation_record = transformer.transform(
                        sample_temp, transformation_record=transformation_records_temp, transformation_value=action
                    )
                    sample_temp = transformed_value
                    transformation_records_temp = new_transformation_record

                sample_temp = self._enforce_dependencies(sample_temp, dependencies)

                # Nawawy's start
                sample_temp = sample_temp.reshape(number_of_instances, backcast, nv)
                new_prediction, logits = model_predict(original_sample[0], torch.from_numpy(sample_temp), original_sample[2], original_sample[3], original_sample[4], original_sample[5], original_sample[6])
                # new_prediction, _, _, _, _ = model_predict(feature_extractor(sample_temp))

                test_prob=[]
                test_logits=[]
                test_truth=[]
                test_prob.extend(new_prediction.data.cpu().numpy())
                test_truth.extend(score_input.data.cpu().numpy())
                test_logits.extend(logits.data.cpu().numpy())

                score = scoring_function(torch.tensor(test_prob), torch.reshape(torch.tensor(test_truth), (len(torch.tensor(test_truth)),1)), torch.tensor(test_logits), True, False)

                # sample_temp = sample_temp.reshape(backcast * nv)
                sample_temp = original_sample[0], torch.from_numpy(sample_temp), original_sample[2], original_sample[3], original_sample[4], original_sample[5], original_sample[6]

                # Nawawy's end
                if self.multi_feature_input:
                    return_values.append(
                        (
                            [transformer_index, input_index],
                            transformer,
                            action,
                            sample_temp,
                            transformation_records_temp,
                            score,
                        )
                    )
                else:
                    return_values.append([None, transformer, action, sample_temp, transformation_records_temp, score])
        return return_values
