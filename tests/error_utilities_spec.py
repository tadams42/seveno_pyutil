from seveno_pyutil.error_utilities import ExceptionsAsErrors, add_error_to


class DescribeExceptionsAsErrors:
    def it_handles_basic_cases(self):
        errors = {}

        with ExceptionsAsErrors(errors) as e:
            raise RuntimeError("ZOMG!")
        errors == {"_schema": ["ZOMG!"]}

        errors = {}
        with ExceptionsAsErrors(errors, subkey="some_name") as e:
            raise RuntimeError("ZOMG!")
        errors == {"some_name": ["ZOMG!"]}

    def it_handles_example_cases(self):
        errors = {
            "person": {
                "email": ["is not an email"],
                "name": ["is too long"],
                "date_of_birth": ["is not a date"],
            },
            "job": ["is not from allowed values list"],
        }

        add_error_to(errors, {"person": {"email": "is from illegal domain"}})

        assert errors == {
            "person": {
                "email": ["is not an email", "is from illegal domain"],
                "name": ["is too long"],
                "date_of_birth": ["is not a date"],
            },
            "job": ["is not from allowed values list"],
        }

        add_error_to(errors, {"person": "is illegally formed"})

        assert errors == {
            "person": {
                "email": ["is not an email", "is from illegal domain"],
                "name": ["is too long"],
                "date_of_birth": ["is not a date"],
                "_schema": ["is illegally formed"],
            },
            "job": ["is not from allowed values list"],
        }

        add_error_to(errors, {"job": {"title": "can't be blank"}})

        assert errors == {
            "person": {
                "email": ["is not an email", "is from illegal domain"],
                "name": ["is too long"],
                "date_of_birth": ["is not a date"],
                "_schema": ["is illegally formed"],
            },
            "job": {
                "_schema": ["is not from allowed values list"],
                "title": ["can't be blank"],
            },
        }

        add_error_to(errors, {"job": {"title": "is overpaid"}})
        add_error_to(errors, {"job": {"title": ["is forbiden", "doesn't exist"]}})

        assert errors == {
            "person": {
                "email": ["is not an email", "is from illegal domain"],
                "name": ["is too long"],
                "date_of_birth": ["is not a date"],
                "_schema": ["is illegally formed"],
            },
            "job": {
                "_schema": ["is not from allowed values list"],
                "title": [
                    "can't be blank",
                    "is overpaid",
                    "is forbiden",
                    "doesn't exist",
                ],
            },
        }

    def it_handles_deeply_nested_case(self):
        errors = {"foo": ["is not bar"]}
        add_error_to(errors, {"foo": {"bar": {"baz": "ZOMG"}}})
        assert errors == {"foo": {"_schema": ["is not bar"], "bar": {"baz": ["ZOMG"]}}}
