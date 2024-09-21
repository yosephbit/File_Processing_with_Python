# local is our default env
env = local

# See https://www.gnu.org/software/make/manual/make.html#Phony-Targets
.PHONY: release
release:
ifeq ($(env), local)
	$(info local build -- containers wont be built and pushed to ECR and no deployment on ECS)
else
	# Enable Docker pushing images to ECR
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.ecr.us-east-1.amazonaws.com

	# building and pushing processing-tools-api to ECR
	docker buildx build --build-arg GIT_SHA=$(shell git rev-parse HEAD) -t $(env)-processing-tools-api --platform linux/amd64 .
	docker tag $(env)-processing-tools-api:latest <account>.ecr.us-east-1.amazonaws.com/<project>-$(env)-processing-tools-api:latest
	docker push <account>.ecr.us-east-1.amazonaws.com/<project>-$(env)-processing-tools-api:latest

	# building and pushing processing-tools-browserless to ECR
	docker pull browserless/chrome:1.51-chrome-stable
	docker tag browserless/chrome:1.51-chrome-stable <account>.ecr.us-east-1.amazonaws.com/<project>-$(env)-processing-tools-browserless:latest
	docker push <account>.ecr.us-east-1.amazonaws.com/<project>-$(env)-processing-tools-browserless:latest

	# deployment of new images to ECS
	$(info shipping to ecs cluster <project>-${env}-processing-tools-workers)
	aws ecs update-service --cluster <project>-${env}-processing-tools-workers --service processing-tools-workers --force-new-deployment
endif
