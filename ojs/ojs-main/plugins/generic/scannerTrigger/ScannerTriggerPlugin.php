<?php

/**
 * @file plugins/generic/scannerTrigger/ScannerTriggerPlugin.php
 *
 * @class ScannerTriggerPlugin
 *
 * @brief Touch a scanner trigger file when OJS renders a page.
 */

namespace APP\plugins\generic\scannerTrigger;

use APP\core\Application;
use PKP\core\PKPPageRouter;
use PKP\plugins\GenericPlugin;
use PKP\plugins\Hook;

class ScannerTriggerPlugin extends GenericPlugin
{
    /**
     * @copydoc Plugin::register()
     *
     * @param null|mixed $mainContextId
     */
    public function register($category, $path, $mainContextId = null)
    {
        if (!parent::register($category, $path, $mainContextId)) {
            return false;
        }

        if ($this->getEnabled($mainContextId)) {
            Hook::add('TemplateManager::display', $this->touchScannerTrigger(...));
        }

        return true;
    }

    public function getDisplayName(): string
    {
        return __('plugins.generic.scannerTrigger.name');
    }

    public function getDescription(): string
    {
        return __('plugins.generic.scannerTrigger.description');
    }

    /**
     * Touch a shared trigger file. The scanner sidecar watches this file and
     * performs the heavy scan outside the OJS request.
     */
    public function touchScannerTrigger(string $hookName, array $args): bool
    {
        $request = Application::get()->getRequest();
        $router = $request->getRouter();

        if (!$router instanceof PKPPageRouter) {
            return false;
        }

        $triggerPath = getenv('OJS_SCANNER_TRIGGER_FILE') ?: '/scan-trigger/ojs-page-trigger.json';
        $throttleSeconds = (int) (getenv('OJS_SCANNER_TRIGGER_THROTTLE_SECONDS') ?: 60);

        if ($triggerPath === '') {
            return false;
        }

        if ($throttleSeconds > 0 && file_exists($triggerPath)) {
            $lastTriggeredAt = @filemtime($triggerPath);
            if ($lastTriggeredAt && time() - $lastTriggeredAt < $throttleSeconds) {
                return false;
            }
        }

        $directory = dirname($triggerPath);
        if (!is_dir($directory)) {
            @mkdir($directory, 0775, true);
        }

        $payload = [
            'triggered_at' => gmdate('c'),
            'page' => $router->getRequestedPage($request),
            'op' => $router->getRequestedOp($request),
        ];

        @file_put_contents($triggerPath, json_encode($payload, JSON_UNESCAPED_SLASHES) . PHP_EOL, LOCK_EX);

        return false;
    }
}
