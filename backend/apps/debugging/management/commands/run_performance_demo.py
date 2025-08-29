"""
Django management command to run the performance monitoring demo
"""

import json
from django.core.management.base import BaseCommand
from apps.debugging.performance_demo import PerformanceDemo


class Command(BaseCommand):
    help = 'Run the performance monitoring demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-file',
            type=str,
            help='Save results to a JSON file',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting Performance Monitoring Demo...')
        )

        try:
            demo = PerformanceDemo()
            results = demo.run_full_demo()

            if options['output_file']:
                with open(options['output_file'], 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                self.stdout.write(
                    self.style.SUCCESS(f'Results saved to {options["output_file"]}')
                )

            if options['verbose']:
                self.stdout.write('\nDetailed Results:')
                self.stdout.write(json.dumps(results, indent=2, default=str))

            self.stdout.write(
                self.style.SUCCESS('\n✅ Performance demo completed successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Demo failed: {str(e)}')
            )
            raise