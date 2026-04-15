.. _generator-metadata:

Customizing synthesis with generator metadata
==============================================

When you use ``generator_config`` to set an entity type to ``Synthesis``, Textual uses default synthesis settings. The ``generator_metadata`` parameter allows you to fine-tune how each entity type's synthesizer behaves.

``generator_metadata`` is a dictionary that maps entity type names (such as ``"NAME_GIVEN"`` or ``"EMAIL_ADDRESS"``) to metadata instances that control synthesis behavior for that type.

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    from tonic_textual.classes.generator_metadata.name_generator_metadata import NameGeneratorMetadata
    from tonic_textual.classes.generator_metadata.email_generator_metadata import EmailGeneratorMetadata

    textual = TextualNer()

    generator_metadata = {
        "NAME_GIVEN": NameGeneratorMetadata(preserve_gender=True),
        "NAME_FAMILY": NameGeneratorMetadata(is_consistency_case_sensitive=True),
        "EMAIL_ADDRESS": EmailGeneratorMetadata(preserve_domain=True),
    }

    result = textual.redact(
        "Contact John Smith at john.smith@example.com",
        generator_default="Synthesis",
        generator_metadata=generator_metadata,
    )

.. note::

    The ``redact_structured`` method takes a single ``Optional[BaseMetadata]`` instead of a dictionary, because it operates on a single entity type at a time.

Common parameters
-----------------

All metadata classes inherit from ``BaseMetadata`` and share the following parameters:

* ``swaps`` (dict of str to str, default ``{}``) -- A dictionary of explicit replacement mappings. When a detected value matches a key, the corresponding value is used as the synthesized replacement instead of a generated one.
* ``constant_value`` (str | None, default ``None``) -- A string value that will be used as the replacement, if there is not a value in ``swaps`` that matches.

.. code-block:: python

    from tonic_textual.classes.generator_metadata.name_generator_metadata import NameGeneratorMetadata

    # Always replace "Acme" with "Globex" instead of generating a random name
    metadata = NameGeneratorMetadata(swaps={"Acme": "Globex"})

    # Always replace names with "Alice"
    metadata = NameGeneratorMetadata(constant_value="Alice")

    # Replace all names with "Bob" except for "Alice" which will be replaced with "Mary"
    metadata = NameGeneratorMetadata(constant_value="Bob", swaps={"Alice": "Mary"})


Name synthesis
--------------

:class:`~tonic_textual.classes.generator_metadata.name_generator_metadata.NameGeneratorMetadata` controls how synthesized names are generated. Use it with the ``NAME_GIVEN`` and ``NAME_FAMILY`` entity types.

* ``is_consistency_case_sensitive`` (bool, default ``False``) -- When ``True``, name consistency is case-sensitive. ``"john"`` and ``"John"`` are treated as different names and might receive different replacements.
* ``preserve_gender`` (bool, default ``False``) -- When ``True``, the synthesized name preserves the gender of the original. Male names are replaced with male names, and female names with female names.

.. code-block:: python

    from tonic_textual.classes.generator_metadata.name_generator_metadata import NameGeneratorMetadata

    generator_metadata = {
        "NAME_GIVEN": NameGeneratorMetadata(preserve_gender=True),
    }

    result = textual.redact(
        "John told Mary about the project.",
        generator_default="Synthesis",
        generator_metadata=generator_metadata,
    )


Email synthesis
---------------

:class:`~tonic_textual.classes.generator_metadata.email_generator_metadata.EmailGeneratorMetadata` controls how synthesized email addresses are generated. Use it with the ``EMAIL_ADDRESS`` entity type.

* ``preserve_domain`` (bool, default ``False``) -- When ``True``, the domain portion of the email address is preserved. For example, ``"john@example.com"`` might become ``"alan@example.com"``.

.. code-block:: python

    from tonic_textual.classes.generator_metadata.email_generator_metadata import EmailGeneratorMetadata

    generator_metadata = {
        "EMAIL_ADDRESS": EmailGeneratorMetadata(preserve_domain=True),
    }

    result = textual.redact(
        "Reach me at john@example.com",
        generator_default="Synthesis",
        generator_metadata=generator_metadata,
    )


Phone number synthesis
----------------------

:class:`~tonic_textual.classes.generator_metadata.phone_number_generator_metadata.PhoneNumberGeneratorMetadata` controls how synthesized telephone numbers are generated. Use it with the ``PHONE_NUMBER`` entity type.

* ``use_us_phone_number_generator`` (bool, default ``False``) -- When ``True``, generated telephone numbers use a US phone number format.
* ``replace_invalid_numbers`` (bool, default ``True``) -- When ``True``, detected telephone numbers that are not valid are still replaced with synthesized values.

.. code-block:: python

    from tonic_textual.classes.generator_metadata.phone_number_generator_metadata import PhoneNumberGeneratorMetadata

    generator_metadata = {
        "PHONE_NUMBER": PhoneNumberGeneratorMetadata(
            use_us_phone_number_generator=True,
            replace_invalid_numbers=True,
        ),
    }

    result = textual.redact(
        "Call me at 555-0123.",
        generator_default="Synthesis",
        generator_metadata=generator_metadata,
    )


Date and time synthesis
-----------------------

:class:`~tonic_textual.classes.generator_metadata.date_time_generator_metadata.DateTimeGeneratorMetadata` controls how synthesized dates and times are generated. Use it with the ``DATE_TIME`` entity type. Dates are shifted by a random number of days within a configurable range.

* ``scramble_unrecognized_dates`` (bool, default ``True``) -- When ``True``, dates that Textual cannot parse into a standard format are scrambled.
* ``additional_date_formats`` (list of str, default ``[]``) -- Additional date format patterns that Textual should recognize. Uses Python ``strftime``/``strptime`` format codes.
* ``apply_constant_shift_to_document`` (bool, default ``False``) -- When ``True``, all dates within the same document are shifted by the same random offset. This preserves the relative time differences between dates.
* ``use_clear_date_and_passthrough_or_group_year_generator`` (bool, default ``False``) -- When ``True``, sets the date to January 1st and if the year is less than 90 years ago, passes through the year. Otherwise, sets the year to the current year minus 90.
* ``metadata`` (:class:`~tonic_textual.classes.generator_metadata.timestamp_shift_metadata.TimestampShiftMetadata`) -- Controls the date shift range. By default, dates shift by -7 to +7 days.

TimestampShiftMetadata
^^^^^^^^^^^^^^^^^^^^^^

:class:`~tonic_textual.classes.generator_metadata.timestamp_shift_metadata.TimestampShiftMetadata` configures the range of days by which dates can be shifted.

* ``left_shift_in_days`` (int, default ``-7``) -- The minimum shift in days. Use a negative value to shift dates into the past.
* ``right_shift_in_days`` (int, default ``7``) -- The maximum shift in days. Use a positive value to shift dates into the future.

.. code-block:: python

    from tonic_textual.classes.generator_metadata.date_time_generator_metadata import DateTimeGeneratorMetadata
    from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata

    generator_metadata = {
        "DATE_TIME": DateTimeGeneratorMetadata(
            apply_constant_shift_to_document=True,
            metadata=TimestampShiftMetadata(
                left_shift_in_days=-30,
                right_shift_in_days=30,
            ),
        ),
    }

    result = textual.redact(
        "The meeting is on 2024-01-15 and the deadline is 2024-02-01.",
        generator_default="Synthesis",
        generator_metadata=generator_metadata,
    )


Person age synthesis
--------------------

:class:`~tonic_textual.classes.generator_metadata.person_age_generator_metadata.PersonAgeGeneratorMetadata` controls how synthesized ages are generated. Use it with the ``PERSON_AGE`` entity type.

* ``scramble_unrecognized_dates`` (bool, default ``True``) -- When ``True``, dates that Textual cannot parse are scrambled.
* ``use_passthrough_or_group_age_generator`` (bool, default ``False``) -- When ``True``, passes through ages 89 or under. Changes other ages to ``"90+"``.
* ``metadata`` (:class:`~tonic_textual.classes.generator_metadata.age_shift_metadata.AgeShiftMetadata`) -- Controls the age shift amount. By default, ages shift by 7 years.

AgeShiftMetadata
^^^^^^^^^^^^^^^^

:class:`~tonic_textual.classes.generator_metadata.age_shift_metadata.AgeShiftMetadata` configures the number of years to shift detected ages.

* ``age_shift_in_years`` (int, default ``7``) -- The number of years to shift the age.

.. code-block:: python

    from tonic_textual.classes.generator_metadata.person_age_generator_metadata import PersonAgeGeneratorMetadata
    from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata

    generator_metadata = {
        "PERSON_AGE": PersonAgeGeneratorMetadata(
            metadata=AgeShiftMetadata(age_shift_in_years=3),
        ),
    }

    result = textual.redact(
        "The patient is 45 years old.",
        generator_default="Synthesis",
        generator_metadata=generator_metadata,
    )


Address synthesis (HIPAA)
-------------------------

:class:`~tonic_textual.classes.generator_metadata.hipaa_address_generator_metadata.HipaaAddressGeneratorMetadata` controls how synthesized addresses are generated for location entity types such as ``LOCATION_ADDRESS`` and ``LOCATION_ZIP``. By default, address synthesis follows HIPAA Safe Harbor de-identification rules.

* ``use_non_hipaa_address_generator`` (bool, default ``False``) -- When ``True``, uses a non-HIPAA-compliant address generator that might produce more realistic addresses, but does not guarantee HIPAA Safe Harbor compliance.
* ``replace_truncated_zeros_in_zip_code`` (bool, default ``True``) -- When ``True``, for ZIP codes that are truncated to three digits (per HIPAA Safe Harbor), the removed digits are replaced with zeros.
* ``realistic_synthetic_values`` (bool, default ``True``) -- When ``True``, generates realistic-looking synthetic address values.
* ``use_three_digit_zips`` (bool, default ``False``) -- When ``True``, zip codes are always truncated to three digits.
* ``replace_foreign_zip_codes_with_zeros`` (bool, default ``False``) -- When ``True``, foreign zip codes become all zeros.

.. code-block:: python

    from tonic_textual.classes.generator_metadata.hipaa_address_generator_metadata import HipaaAddressGeneratorMetadata

    generator_metadata = {
        "LOCATION_ADDRESS": HipaaAddressGeneratorMetadata(
            realistic_synthetic_values=True,
            replace_truncated_zeros_in_zip_code=True,
        ),
    }

    result = textual.redact(
        "She lives at 123 Main St, Springfield, IL 62704.",
        generator_default="Synthesis",
        generator_metadata=generator_metadata,
    )


Numeric value synthesis
-----------------------

:class:`~tonic_textual.classes.generator_metadata.numeric_value_generator_metadata.NumericValueGeneratorMetadata` controls how synthesized numeric values are generated. Use it with the ``NUMERIC_VALUE`` entity type.

* ``use_oracle_integer_pk_generator`` (bool, default ``False``) -- When ``True``, uses a generator designed for Oracle integer primary keys.

.. code-block:: python

    from tonic_textual.classes.generator_metadata.numeric_value_generator_metadata import NumericValueGeneratorMetadata

    generator_metadata = {
        "NUMERIC_VALUE": NumericValueGeneratorMetadata(
            use_oracle_integer_pk_generator=True,
        ),
    }


Combining multiple metadata configurations
-------------------------------------------

You can combine multiple metadata configurations in a single call. This example configures synthesis for names, emails, and dates:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    from tonic_textual.classes.generator_metadata.name_generator_metadata import NameGeneratorMetadata
    from tonic_textual.classes.generator_metadata.email_generator_metadata import EmailGeneratorMetadata
    from tonic_textual.classes.generator_metadata.date_time_generator_metadata import DateTimeGeneratorMetadata
    from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata

    textual = TextualNer()

    result = textual.redact(
        "John Smith (john@acme.com) joined on 2024-01-15.",
        generator_default="Off",
        generator_config={
            "NAME_GIVEN": "Synthesis",
            "NAME_FAMILY": "Synthesis",
            "EMAIL_ADDRESS": "Synthesis",
            "DATE_TIME": "Synthesis",
        },
        generator_metadata={
            "NAME_GIVEN": NameGeneratorMetadata(preserve_gender=True),
            "EMAIL_ADDRESS": EmailGeneratorMetadata(preserve_domain=True),
            "DATE_TIME": DateTimeGeneratorMetadata(
                apply_constant_shift_to_document=True,
                metadata=TimestampShiftMetadata(
                    left_shift_in_days=-14,
                    right_shift_in_days=14,
                ),
            ),
        },
    )
