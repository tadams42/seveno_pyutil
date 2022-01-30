from seveno_pyutil import in_batches


class DescribeInBatches:
    def it_iterates_iterator_in_batches(self):
        g = (o for o in range(10))
        result = []
        for batch in in_batches(g, of_size=3):
            result.append(list(batch))

        assert result == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

    def it_iterates_list_in_batches(self):
        g = list(range(10))
        result = []
        for batch in in_batches(g, of_size=3):
            result.append(list(batch))

        assert result == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

    def it_changes_resulting_batch_size_when_individual_batches_are_not_fully_consumed(
        self,
    ):
        g = list(range(10))
        result = []
        for batch in in_batches(g, of_size=3):
            result.append([next(batch), next(batch)])

        assert result == [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]
