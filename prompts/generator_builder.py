from __future__ import annotations
import logging

from dynamicprompts.generators import (
    DummyGenerator,
    FeelingLuckyGenerator,
    RandomPromptGenerator,
    CombinatorialPromptGenerator,
    BatchedCombinatorialPromptGenerator,
    PromptGenerator,
    JinjaGenerator
)

from dynamicprompts.generators.magicprompt import MagicPromptGenerator
from dynamicprompts.generators.attentiongenerator import AttentionGenerator

logger = logging.getLogger(__name__)


class GeneratorBuilder:
    def __init__(self, wildcard_manager, ignore_whitespace=False):
        self._wildcard_manager = wildcard_manager

        self._is_dummy = False
        self._is_feeling_lucky = False
        self._is_jinja_template = False
        self._is_combinatorial = False
        self._is_magic_prompt = False
        self._is_attention_grabber = False

        self._combinatorial_batches = 1
        self._magic_prompt_length = 100
        self._magic_temp_value = 0.7
        self._min_attention = 1.1
        self._max_attention = 1.5
        self._device = 0
        self._ignore_whitespace = ignore_whitespace

    def log_configuration(self):
        logger.debug(
            f"""
        Creating generator:
            is_dummy: {self._is_dummy}
            is_feeling_lucky: {self._is_feeling_lucky}
            enable_jinja_templates: {self._is_jinja_template}
            is_combinatorial: {self._is_combinatorial}
            is_magic_prompt: {self._is_magic_prompt}
            combinatorial_batches: {self._combinatorial_batches}
            magic_prompt_length: {self._magic_prompt_length}
            magic_temp_value: {self._magic_temp_value}
            is_attention_grabber: {self._is_attention_grabber}
            min_attention: {self._min_attention}
            max_attention: {self._max_attention}

        """
        )

    def set_is_dummy(self, is_dummy=True):
        self._is_dummy = is_dummy
        return self

    def set_is_feeling_lucky(self, is_feeling_lucky=True):
        self._is_feeling_lucky = is_feeling_lucky
        return self

    def set_is_attention_grabber(
        self, is_attention_grabber=True, min_attention=1.1, max_attention=1.5
    ):
        self._is_attention_grabber = is_attention_grabber
        self._min_attention = min_attention
        self._max_attention = max_attention
        return self

    def set_is_jinja_template(self, is_jinja_template=True):
        self._is_jinja_template = is_jinja_template
        return self

    def set_is_combinatorial(self, is_combinatorial=True, combinatorial_batches=1):
        self._is_combinatorial = is_combinatorial
        self._combinatorial_batches = combinatorial_batches
        return self

    def set_is_magic_prompt(
        self, is_magic_prompt=True, magic_prompt_length=100, magic_temp_value=0.7, device=0
    ):
        self._magic_prompt_length = magic_prompt_length
        self._magic_temp_value = magic_temp_value
        self._is_magic_prompt = is_magic_prompt
        self._device = device

        return self

    def create_generator(
        self,
        original_seed,
        context,
        unlink_seed_from_prompt=False,
    ):

        if self._is_dummy:
            return DummyGenerator()

        elif self._is_feeling_lucky:
            generator = FeelingLuckyGenerator()

        elif self._is_jinja_template:
            generator = self.create_jinja_generator(context)
        else:
            generator = self.create_basic_generator(
                original_seed,
                unlink_seed_from_prompt,
            )

        if self._is_magic_prompt:
            generator = MagicPromptGenerator(
                generator,
                self._device,
                self._magic_prompt_length,
                self._magic_temp_value,
                seed=original_seed,
            )

        if self._is_attention_grabber:
            generator = AttentionGenerator(
                generator,
                min_attention=self._min_attention,
                max_attention=self._max_attention,
            )
        return generator

    def create_basic_generator(
        self,
        original_seed: int,
        unlink_seed_from_prompt: bool = False,
    ) -> PromptGenerator:
        if self._is_combinatorial:
            prompt_generator = CombinatorialPromptGenerator(self._wildcard_manager, ignore_whitespace=self._ignore_whitespace)
            prompt_generator = BatchedCombinatorialPromptGenerator(
                prompt_generator, self._combinatorial_batches
            )
        else:
            prompt_generator = RandomPromptGenerator(
                self._wildcard_manager, original_seed, unlink_seed_from_prompt, ignore_whitespace=self._ignore_whitespace
            )

        return prompt_generator

    def create_jinja_generator(self, p) -> PromptGenerator:
        original_prompt = p.all_prompts[0] if len(p.all_prompts) > 0 else p.prompt
        original_negative_prompt = (
            p.all_negative_prompts[0]
            if len(p.all_negative_prompts) > 0
            else p.negative_prompt
        )
        context = {
            "model": {
                "filename": p.sd_model.sd_checkpoint_info.filename,
                "title": p.sd_model.sd_checkpoint_info.title,
                "hash": p.sd_model.sd_checkpoint_info.hash,
                "model_name": p.sd_model.sd_checkpoint_info.model_name,
            },
            "image": {
                "width": p.width,
                "height": p.height,
            },
            "parameters": {
                "steps": p.steps,
                "batch_size": p.batch_size,
                "num_batches": p.n_iter,
                "width": p.width,
                "height": p.height,
                "cfg_scale": p.cfg_scale,
                "sampler_name": p.sampler_name,
                "seed": p.seed,
            },
            "prompt": {
                "prompt": original_prompt,
                "negative_prompt": original_negative_prompt,
            },
        }

        generator = JinjaGenerator(self._wildcard_manager, context)
        return generator
